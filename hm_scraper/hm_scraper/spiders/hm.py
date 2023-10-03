import json
import re
from time import sleep
import scrapy
from scrapy import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import os
import time
import signal
from ..items import HmScraperItem

ALLOWED_CATEGORIES = ["women", "divided", "men"]
DISALLOWED_SUB_CATEGORIES = ["shoes", "accessories", "care", "beauty", "dog"]
FIT_KEYWORDS = ["Maternity", "Petite", "Plus Size", "Curvy", "Tall"]
NECK_LINE_KEYWORDS = ["Scoop", "Round Neck," "U Neck", "U-Neck", "V Neck",
                      "V-neck", "V Shape", "V-Shape", "Deep", "Plunge", "Square",
                      "Straight", "Sweetheart", "Princess", "Dipped", "Surplice",
                      "Halter", "Asymetric", "One-Shoulder", "One Shoulder",
                      "Turtle", "Boat", "Off- Shoulder", "Collared", "Cowl", "Neckline"]

OCCASIONS_KEYWORDS = ["office", "work", "smart", "workwear", "wedding", "nuptials",
                      "night out", "evening", "spring", "summer", "day", "weekend",
                      "outdoor", "outdoors", "adventure", "black tie", "gown",
                      "formal", "cocktail", "date night", "vacation", "vacay", "fit",
                      "fitness", "athletics", "athleisure", "work out", "sweat",
                      "swim", "swimwear", "lounge", "loungewear"]

LENGTH_KEYWORDS = ["length", "mini", "short", "maxi", "crop", "cropped", "sleeves",
                   "tank", "top", "three quarter", "ankle", "long"]

STYLE_KEYWORDS = ["bohemian", "embellished", "sequin", "floral", "off shoulder",
                  "puff sleeve", "bodysuit", "shell", "crop", "corset", "tunic",
                  "bra", "camisole", "polo", "aviator", "shearling", "sherpa",
                  "biker", "bomber", "harrington", "denim", "jean", "leather",
                  "military", "quilted", "rain", "tuxedo", "windbreaker", "utility",
                  "duster", "faux fur", "overcoat", "parkas", "peacoat", "puffer",
                  "skater", "trench", "Fleece", "a line", "bodycon", "fitted",
                  "high waist", "high-low", "pencil", "pleat", "slip", "tulle",
                  "wrap", "cargo", "chino", "skort", "cigarette", "culottes",
                  "flare", "harem", "relaxed", "skinny", "slim", "straight leg",
                  "tapered", "wide leg", "palazzo", "stirrup", "bootcut", "boyfriend",
                  "loose", "mom", "jeggings", "backless", "bandage", "bandeau",
                  "bardot", "one-shoulder", "slinger", "shift", "t-shirt", "smock",
                  "sweater", "gown"]

AESTHETIC_KEYWORDS = ["E-girl", "VSCO girl", "Soft Girl", "Grunge", "CottageCore",
                      "Normcore", "Light Academia", "Dark Academia ", "Art Collective",
                      "Baddie", "WFH", "Black", "fishnet", "leather"]

NEGLECT_CATEGORIES_LIST = ['New in', 'Joggers', 'Multipacks', 'new-in',
                           'Socks', 'Exclusives at ASOS', 'Tracksuits & Joggers',
                           "Sportswear", "co-ords", "exclusives", "shoes", "accessories",
                           "heels", "snickers", "earrings", "shoes", "accessories", "care", "beauty", "dog"]


class HmSpider(CrawlSpider):
    name = 'hm'
    allowed_domains = ['www2.hm.com']

    rules = (
        Rule(LinkExtractor(allow=r'productpage.*'), callback='parse_product'),
    )

    def __init__(self, *a, **kw):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
        options.add_argument(f'user-agent={user_agent}')
        time.sleep(5)
        crawler_env = os.environ.get('STANDALONE_SELENIUM_CHROME_DRIVER')
        if (crawler_env and crawler_env == "True"):
            self.driver = webdriver.Remote(command_executor=f"{os.environ.get('URI')}",
                                           options=options)
        else:
            self.driver = webdriver.Chrome(
                ChromeDriverManager().install(), options=options)
        self.driver.maximize_window()
        super().__init__(*a, **kw)

    def start_requests(self):
        base_url = "https://www2.hm.com/en_us/women/new-arrivals/clothes.html"
        signal.signal(signal.SIGINT, self.handle_interrupt)
        yield scrapy.Request(url=base_url, callback=self.parse_pages)

    # This method will be called when the spider is closed by SIGINT

    def handle_interrupt(self, signum, frame):
        self.graceful_terminate()
        os.kill(os.getpid(), signal.SIGKILL)

    # Helper for interrupt handler

    def graceful_terminate():
        try:
            with open('output.json', 'r') as json_file:
                data = json_file.read()

            data = data.strip()
            # Remove the trailing comma if it exists
            if re.search(',', data[-1], re.IGNORECASE):
                data = data[:-1]

            # Add the closing bracket
            data += ']' if (not re.search(']',
                            data[-1], re.IGNORECASE)) else ''

            # Write the modified data back to the file
            with open('output.json', 'w') as json_file:
                json_file.write(data)
        except Exception as e:
            print(f"Error finishing JSON file: {e}")

    def parse_pages(self, response):
        total_items = response.css(
            "h2.load-more-heading[data-total]::attr('data-total')").get()
        if total_items:
            total_items = int(total_items.strip())
            for page in range(36, total_items + 1, 36):
                url = f"https://www2.hm.com/en_us/women/new-arrivals/clothes.html?page-size={page}"
                yield scrapy.Request(url=url, callback=self.parse_product_links)

        pass

    def parse_product_links(self, response):
        product_links = response.css(
            "ul.products-listing li div a.item-link::attr('href')").getall()
        if product_links:
            for link in product_links:
                if (not self.in_neglected_categories(link)):
                    yield scrapy.Request(url=f"https://www2.hm.com{link}", callback=self.parse_product)

    def check_disallowed_categories(self, categories_data):
        for element in categories_data["links"]:
            value = element["label"]
            if value.lower() in DISALLOWED_SUB_CATEGORIES:
                return False

        return True

    def parse_product(self, response):
        url = response.request.url
        self.driver.get(url)
        sleep(4)
        custom_selector = Selector(text=self.driver.page_source)

        categories_raw_data = response.xpath(
            "//script[contains(., 'breadcrumb')]/text()").get()
        categories, gender, cleaned_categories_data = self.get_categories(
            categories_raw_data)
        check_disallowed = self.check_disallowed_categories(
            cleaned_categories_data)

        if check_disallowed:
            name = response.css("section.product-name-price h1::text").get()
            price = response.css(".product-item-price>span::text").get()
            price = price.strip() if price else price
            colors = response.xpath('//a[@data-color]/@data-color').getall()
            details = response.css(
                "div#section-descriptionAccordion *::text").getall()
            details = [detail.strip() for detail in details]
            details = [detail for detail in details if detail]
            sizes = self.get_sizes()

            raw_details_keys = response.css(
                '.details-attributes-list-item>dt::text').getall()
            raw_details_values = response.css(
                '.details-attributes-list-item>dd::text').getall()
            raw_details_element = response.css(
                '.details-attributes-list-item').getall()
            raw_details = self.clean_raw_details(
                raw_details_values, raw_details_keys, raw_details_element)

            details_meta = list(raw_details.values())+details

            external_id = url.split(".")[-2]
            if not external_id:
                external_id = raw_details.get("Art. No.", "")
                external_id = external_id if external_id else raw_details.get(
                    "Article number:", "")

            fabric = self.find_fabric_from_details(details_meta)
            images = self.get_images(custom_selector)
            number_of_reviews, review_description = self.get_review_data(
                custom_selector)
            top_best_seller = ""
            fit = ' '.join(self.find_keywords_from_str(
                details_meta, FIT_KEYWORDS)).strip()
            neck_line = ' '.join(self.find_keywords_from_str(
                details_meta, NECK_LINE_KEYWORDS)).strip()
            length = ' '.join(self.find_keywords_from_str(
                details_meta, LENGTH_KEYWORDS)).strip()

            occasions = self.find_keywords_from_str(
                details_meta, OCCASIONS_KEYWORDS)
            style = self.find_keywords_from_str(
                details_meta, STYLE_KEYWORDS)
            # aesthetics = self.get_aesthetics(details, name, categories)

            website_name = "hm"
            item = HmScraperItem()
            item["external_id"] = external_id
            item["url"] = url
            item["name"] = name
            item["categories"] = categories
            item["price"] = price.strip()
            item["colors"] = colors
            item["sizes"] = sizes
            item["fabric"] = ", ".join(fabric) if type(
                fabric) is list else fabric
            item["fit"] = fit
            item["details"] = details
            item["images"] = images
            item["number_of_reviews"] = number_of_reviews
            item["review_description"] = review_description
            item["top_best_seller"] = top_best_seller
            item["style"] = style
            item["length"] = length
            item["neck_line"] = neck_line
            item["occasions"] = occasions
            # item["aesthetics"] = aesthetics
            item["gender"] = gender
            item["meta"] = {}
            item["website_name"] = website_name

            if categories and not self.in_disallowed_categories(name, url, categories):
                yield item

    def in_disallowed_categories(self, name, url, categories):
        for keyword in NEGLECT_CATEGORIES_LIST:
            if re.search(keyword, name, re.IGNORECASE) or \
                    re.search(keyword, url, re.IGNORECASE) or \
                    re.search(keyword, ' '.join(categories), re.IGNORECASE):
                return True
            return False

    def clean_raw_details(self, raw_details_values, raw_details_keys, raw_details_element):
        result = {}
        value_index = 0
        for i in range(len(raw_details_keys)):
            value_count = raw_details_element[i].count("</dd>")
            if value_count == 1:
                result[raw_details_keys[i]] = raw_details_values[value_index]
                value_index += 1
            else:
                values = raw_details_values[i:i+value_count]
                result[raw_details_keys[i]] = values
                value_index += value_count

        return result

    def get_images(self, custom_selector):
        sleep(1)
        images_source = custom_selector.css(
            ".pdp-image>img::attr(src)").getall()
        images = ["https:" + image for image in images_source]

        return images

    def get_categories(self, raw_data):
        if not raw_data:
            return []
        categories = []
        gender = ""
        cleaned_data = {}
        try:
            cleaned_data = re.findall(r"{.*}", raw_data)[0]
            cleaned_data = json.loads(cleaned_data)
            categories.append(cleaned_data["links"][2]["label"])
            categories.append(cleaned_data["links"][3]["label"])
            gender = cleaned_data["links"][1]["label"]
        except:
            return []
        return categories, gender, cleaned_data

    def get_sizes(self):
        sleep(1)
        size_element = self.driver.find_element(By.CSS_SELECTOR,
                                                ".trigger-button")
        size_location = size_element.location["y"]
        self.driver.execute_script(f"window.scrollTo(0, {size_location})")
        sleep(1)
        size_element.click()
        sleep(1)
        sizes = self.driver.find_elements(By.CSS_SELECTOR,
                                          ".picker-option>button>span.value")
        size_list = [size.text for size in sizes if size.text != "Select size"]
        sleep(1)
        close_button = self.driver.find_element(By.XPATH,
                                                '//*[@id="picker-1"]/div[1]/button')
        close_button.click()

        return size_list

    def get_review_data(self, custom_selector):
        sleep(1)
        number_of_reviews = ""
        review_description = []

        if "data-rating" in custom_selector.xpath('//*[@id="reviews-trigger"]').get():
            review_button = self.driver.find_element(By.XPATH,
                                                     '//*[@id="reviews-trigger"]//button')
            self.driver.execute_script(
                f"window.scrollTo(0, {review_button.location['y']})")
            sleep(1)
            number_of_reviews = re.findall(r'\d+', review_button.text)[0]
            review_button.click()
            sleep(1)

            while len(self.driver.find_elements(By.XPATH, '//*[@id="portal"]/div/div[1]/div[3]/div/div/button')) > 0:
                show_more_button = self.driver.find_elements(By.XPATH,
                                                             '//*[@id="portal"]/div/div[1]/div[3]/div/div/button')
                self.driver.execute_script(
                    f"window.scrollTo(0, {show_more_button[0].location['y']})")
                show_more_button[0].click()
                sleep(1)

            reviews = self.driver.find_elements(By.XPATH,
                                                '//*[contains(@class, "ReviewsList-module--reviewContent")]')
            for review in reviews:
                if "Show more" in review.text:
                    review_description.append(
                        review.text.replace("Show more", ""))
                else:
                    review_description.append(review.text)

        return number_of_reviews, review_description

    def in_neglected_categories(self, category):
        for neglected_cat in NEGLECT_CATEGORIES_LIST:
            if re.search(neglected_cat, category, re.IGNORECASE):
                return True

        return False

     # This helper finds fabric from details and returns it
    def find_fabric_from_details(self, details):
        product_details = ' '.join(details)
        fabrics_founded = re.findall(r"""(\d+ ?%\s?)?(
            velvet\b|silk\b|satin\b|cotton\b|lace\b|
            sheer\b|organza\b|chiffon\b|spandex\b|polyester\b|
            poly\b|linen\b|nylon\b|viscose\b|Georgette\b|Ponte\b|
            smock\b|smocked\b|shirred\b|Rayon\b|Bamboo\b|Knit\b|Crepe\b|
            Leather\b|polyamide\b|Acrylic\b|Elastane\bTencel\bCashmere\b|Polyurethane\b|Rubber\b|Lyocell\b)\)?""", product_details,
                                     flags=re.IGNORECASE | re.MULTILINE)
        fabric_tuples_joined = [''.join(tups) for tups in fabrics_founded]
        # Removing duplicates now if any
        fabrics_final = []
        for fabric in fabric_tuples_joined:
            if fabric not in fabrics_final:
                fabrics_final.append(fabric)

        return ' '.join(fabrics_final).strip()

    def find_keywords_from_str(self, details, keywords):
        finals = []
        details = ' '.join(details)
        for keyword in keywords:
            if re.search(keyword, details, re.IGNORECASE):
                if keyword not in finals:
                    finals.append(keyword)

        return finals

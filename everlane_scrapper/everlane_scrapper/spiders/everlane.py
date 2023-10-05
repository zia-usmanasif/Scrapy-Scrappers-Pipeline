import scrapy
import json
import re
import os
import time
import signal
from scrapy import Selector
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from ..items import EverlaneScrapperItem

# Constants
WEBSITE_NAME = "everlane"

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

NEGLECT_CATEGORIES_LIST = ['earrings', 'new-in', 'shoe', 'sandal', 'jogger', 'snickers', 'Multipacks', 'DESIGNER', 'heels', 'co-ords', 'joggers', 'Joggers',
                           'Sportswear', 'accessories', 'shoes', 'sandals', 'PROMOTION', 'New in', 'Tracksuits & Joggers', 'exclusives', 'BRANDS', 'Socks', 'Exclusives at ASOS']


class EverlaneSpider(scrapy.Spider):
    name = "everlane"
    allowed_domains = ["www.everlane.com"]

    def __init__(self, *a, **kw):
        options = Options()
        options.add_argument('--head')
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
        url = "https://www.everlane.com/collections/womens-all"
        signal.signal(signal.SIGINT, self.handle_interrupt)
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        self.driver.get(response.request.url)
        self.driver.implicitly_wait(2)
        self.scroll_to_bottom()
        product_links = self.driver.find_elements(
            By.CSS_SELECTOR, 'div.styles_product-details__info__yn3S2 a')
        if (product_links):
            product_links = [link.get_attribute(
                'href') for link in product_links]

            for link in product_links:
                yield scrapy.Request(url=link, callback=self.parse_product)

    def parse_product(self, response):
        try:
            self.driver.get(response.url)
            self.driver.implicitly_wait(2)
            custom_response = Selector(text=self.driver.page_source)
            url = response.url
            name = response.xpath(
                "//meta[@property='og:title'] /@content").get()
            details = response.xpath(
                "//meta[@property='og:description'] /@content").getall()
            external_id = custom_response.xpath(
                "//meta[@itemprop='sku'] /@content").get()
            price = custom_response.response.xpath(
                "//meta[@itemprop='highPrice'] /@content").get()

            colors = custom_response.css(
                "a.styles_color-pip__link__ki0Dp::attr('href')").getall()
            colors = ["-".join(color.split('?')[0].split('-')[-1:-3:-1])
                      for color in colors]
            sizes = custom_response.css(
                "button.styles_product-size__1TPVH::text").getall()
            sizes = [size.strip() for size in sizes if not re.search(
                'notify', size, re.IGNORECASE) or
                not re.search('sold out', size, re.IGNORECASE) or
                not re.search('out of stock', size, re.IGNORECASE) or
                not re.search('few pieces left', size, re.IGNORECASE)]
            images = custom_response.xpath(
                "//meta[@itemprop='image'] /@content").getall()

            categories = custom_response.xpath(
                "//ul[contains(@class, 'styles_breadcrumbs')] /li /a /span /text()").getall()
            if categories:
                categories = [categories[-2]] if len(
                    categories) > 2 else [categories[-1]]

            more_details_btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'More Detail ')]")
            if more_details_btn:
                more_details_btn.click()
            time.sleep(2)

            fabric = self.driver.find_element(
                By.XPATH, "//div[contains(text(), 'Materials')] /.. /div[2] /div")
            fabric = fabric.text if fabric else ""

            details_meta = custom_response.css(
                "div.styles_product-details__opMqB *::text").getall()
            details_meta = details+details_meta
            occasions = self.find_keywords_from_str(
                details_meta, OCCASIONS_KEYWORDS)
            style = self.find_keywords_from_str(details_meta, STYLE_KEYWORDS)
            fit = ' '.join(self.find_keywords_from_str(
                details_meta, FIT_KEYWORDS)).strip()
            neck_line = ' '.join(self.find_keywords_from_str(
                details_meta, NECK_LINE_KEYWORDS)).strip()
            length = ' '.join(self.find_keywords_from_str(
                details_meta, LENGTH_KEYWORDS)).strip()

            fabric = self.find_fabric_from_details(
                details_meta) if not fabric else fabric

            review_descriptions = custom_response.css(
                "div.bv-content-summary-body-text p::text").getall()
            no_reviews = str(len(review_descriptions)
                             ) if review_descriptions else ""

            item = EverlaneScrapperItem()
            item["url"] = response.request.url
            item["external_id"] = external_id
            item["categories"] = categories
            item["name"] = name
            item["price"] = price
            item["colors"] = colors
            item["sizes"] = sizes
            item["details"] = details
            item["fabric"] = fabric
            item["images"] = images
            item["fit"] = fit
            item["neck_line"] = neck_line
            item["length"] = length
            item["gender"] = "women"
            item["number_of_reviews"] = no_reviews
            item["review_description"] = review_descriptions
            item["top_best_seller"] = ""
            item["meta"] = {}
            item["occasions"] = occasions
            item["style"] = style
            item["website_name"] = WEBSITE_NAME
            if not self.in_disallowed_keywords(response.request.url, name, categories) and colors and sizes and details:
                yield item

        except NoSuchElementException:
            pass

    def in_disallowed_keywords(self, url, name, categories):
        categories = ','.join(categories)
        for keyword in NEGLECT_CATEGORIES_LIST:
            if re.search(keyword, url, re.IGNORECASE) or re.search(keyword, name, re.IGNORECASE) or \
                    re.search(keyword, categories, re.IGNORECASE):
                return True
        return False

    def find_keywords_from_str(self, details, keywords):
        finals = []
        details = ' '.join(details)
        for keyword in keywords:
            if re.search(keyword, details, re.IGNORECASE):
                if keyword not in finals:
                    finals.append(keyword)

        return finals

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

     # This method will be called when the spider is closed by SIGINT

    def handle_interrupt(self, signum, frame):
        self.graceful_terminate()
        os.kill(os.getpid(), signal.SIGKILL)

    # Helper for interrupt handler

    def graceful_terminate(self):
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

    def scroll_to_bottom(self):
        last_height = self.driver.execute_script(
            "return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight-100);")

            # Wait to load page
            time.sleep(5)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script(
                "return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def load_reviews(self):
        try:
            reviews_btn = self.driver.find_element(
                By.CSS_SELECTOR, "button.bv-content-btn-pages")

            while reviews_btn:
                reviews_btn.click()
                time.sleep(2)
                reviews_btn = self.driver.find_element(
                    By.CSS_SELECTOR, "button.bv-content-btn-pages")

            time.sleep(2)
            reviews = self.driver.find_elements(
                By.CSS_SELECTOR, "div.bv-content-summary-body-text p")
            return [review.text for review in reviews]

        except NoSuchElementException:
            return []

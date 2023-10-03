import math
import json
import re
import scrapy
from scrapy import Selector
from scrapy.spiders import CrawlSpider
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
from itertools import chain
from ..items import AsosScrapperItem
import os
import signal

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
                           "heels", "snickers", "earrings"]

DISALLOWED_KEYWORDS = ["jogger", "joggers", "sandals", "sandal", "shoe",
                       "shoes", "heels", "accessories", "earrings", "PROMOTION", "DESIGNER", "BRANDS", "snickers",
                       "earrings", "new-in"]

CATEGORY_KEYWORDS = ["Mini Dress", "Midi Dress", "Maxi Dress", "Petite", "Maternity", "Linen", "Tops",
                     "Shorts", "Jeans", "Jumpsuits", "Rompers", "Swimwear", "Blouses", "Blazer", "Pants", "Jackets",
                     "Coats", "Hoodies", "Lingere", "Loungewear"]


WEBSITE_NAME = "Asos"


class AsosSpider(CrawlSpider):
    name = 'asos'
    allowed_domains = ['asos.com']

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
        url = "https://www.asos.com/us/women"
        signal.signal(signal.SIGINT, self.handle_interrupt)
        yield scrapy.Request(url=url, callback=self.parse_categories)

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

    def parse_categories(self, response):
        categories = response.xpath(
            "//span[contains(text(), 'SHOP BY PRODUCT')]/../../ul/li/a/@href").extract()
        if (categories):
            categories = categories[2: 31]

        for category in categories:
            if not self.in_neglected_categories(category):
                yield scrapy.Request(url=category, callback=self.parse_pages)

    def parse_pages(self, response):
        per_page_products = response.xpath(
            "//p[contains(text(), 'viewed')]/text()").extract()

        per_page_products = int(per_page_products[0].split(" ")[
                                2].replace(",", "")) if per_page_products else 0

        products = response.xpath(
            "//p[contains(text(), 'styles found')]/text()").extract()

        products = int(products[0].split(" ")[0].replace(",", "")
                       ) if products else per_page_products
        pageno = 0
        per_page_products = per_page_products if per_page_products else 72
        for _ in range(pageno, products, per_page_products):
            current_page = f"{response.request.url}&page={pageno}"
            pageno += 1
            yield scrapy.Request(url=current_page, callback=self.get_all_products, dont_filter=True)

    def get_all_products(self, response):
        products = response.xpath("//article/a/@href").extract()
        for product_url in products:
            if not self.in_neglected_categories(product_url):
                yield scrapy.Request(url=product_url, callback=self.parse_item)

    def parse_item(self, response):
        try:
            custom_response = self.get_custom_selector(response)
            meta = {}
            json_data = json.loads(response.css(
                "script#split-structured-data::text").get())
            if json_data:
                meta = json_data['@graph'][0] if (
                    '@graph' in json_data.keys()) else json_data

            external_id = str(meta['productID']) if meta['productID'] else ''
            name = meta['name'] if meta['name'] else response.css(
                "title::text").get()
            price = custom_response.xpath(
                "//span[contains(@data-testid, 'current-price')]/text()").extract()

            price = str(price[0]) if price else "0"
            sizes = custom_response.css(
                "select#variantSelector option::text").getall()

            sizes = [size.strip() for size in sizes if
                     not re.search("\w*Out of stock", size) and not re.search("Please select", size)]

            details = self.clean_details(response.xpath(
                "//button[contains(@aria-controls,'productDescriptionDetails')]/../../div//ul/li/text()").extract())
            images = custom_response.xpath(
                "//img[@class='gallery-image'] /@srcset").getall()
            if images:
                images = [image.split(",")[-1] for image in images]
                images = [image for image in images if re.search(
                    "1926w", image, re.IGNORECASE)]
            categories = response.xpath(
                "//nav[@aria-label='breadcrumbs'] /ol /li /a /text()").getall()[1:]
            categories = [re.sub("&|New In:|New In", "", cat)
                          for cat in categories]
            if not categories:
                for keyword in CATEGORY_KEYWORDS:
                    if re.search(keyword, name, re.IGNORECASE) or re.search(keyword, response.request.url, re.IGNORECASE):
                        categories.append(keyword)

            categories = self.clean_categories(categories)
            colors = custom_response.css("span.product-colour::text").getall()
            if colors:
                colors = [color.strip() for color in colors]
                colors = list(set(colors))
            else:
                colors = custom_response.xpath(
                    "//div[contains(@data-testid, 'productColour')] /p /text()").extract()
            extra_details = response.xpath(
                "//div[@id='productDescription']//text()").extract()
            fabric = self.find_fabric_from_details(extra_details)
            extra_details += details

            fit = ' '.join(self.find_keywords_from_str(
                extra_details, FIT_KEYWORDS)).strip()
            neck_line = ' '.join(self.find_keywords_from_str(
                extra_details, NECK_LINE_KEYWORDS)).strip()
            length = ' '.join(self.find_keywords_from_str(
                extra_details, LENGTH_KEYWORDS)).strip()

            gender = "women"
            number_of_reviews = ""
            review_description = []
            top_best_seller = ""
            occasions = self.find_keywords_from_str(
                extra_details, OCCASIONS_KEYWORDS)
            style = self.find_keywords_from_str(extra_details, STYLE_KEYWORDS)

            item = AsosScrapperItem()
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
            item["gender"] = gender
            item["number_of_reviews"] = number_of_reviews
            item["review_description"] = review_description
            item["top_best_seller"] = top_best_seller
            item["meta"] = meta
            item["occasions"] = occasions
            item["style"] = style
            item["website_name"] = WEBSITE_NAME
            if not self.in_disallowed_keywords(response.request.url, name, categories) and colors and sizes and details:
                yield item
        except Exception as e:
            print(e)

    # Helpers

    def get_selector(self, url):
        self.driver.get(url)
        custom_selector = Selector(text=self.driver.page_source)
        return custom_selector

    def extract_last_page(self, response):
        pages_info = response.css('.XmcWz6U::text').get()
        if pages_info:
            get_numbers = re.findall(r'[\d,]+[,\d]', pages_info)
            rs = [int(s.replace(",", "")) for s in get_numbers]
            last_page = rs[1] / rs[0]
            return math.ceil(last_page)
        else:
            return 1

    def extract_info(self, details, keywords):
        for detail in details:
            if any(keyword in detail for keyword in keywords):
                return detail.strip()

    # This helper method clean details we have scrapped
    def clean_details(self, details):
        details = [detail.strip() for detail in details]
        return [detail for detail in details if detail != "" and
                not re.search("Model", detail, re.IGNORECASE) and
                not re.search("Show More", detail, re.IGNORECASE) and
                not re.search("Show less", detail, re.IGNORECASE) and
                not re.search("Product Details", detail, re.IGNORECASE) and
                not re.search("\.", detail, re.IGNORECASE) and
                not re.search("By", detail, re.IGNORECASE)]

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

    # This function scrolls product detail page to the bottom

    def scroll(self):
        last_height = self.driver.execute_script(
            "return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(5)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script(
                "return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    """
    this function returns upper limit of page, for example if we have total of 90 products with 20 products on each
    and page query is like 0 to 20, then 20 to 40 and so on, a time will come when we have 80 to 100 as a page query
    but products are only 90, so this function makes sure we have correct upper limit for pages query, in our case 80-90
    """

    def get_pages_upperlimit(self, current_page, total_pages):
        if (current_page + 72) > total_pages:
            return current_page + (total_pages - current_page)
        else:
            return current_page + 72

    def clean_category_name(self, name):
        if re.search("&", name):
            return name.split("&")
        else:
            return name

    # This function returns custom selector based on selenium request
    def get_custom_selector(self, response):
        self.driver.get(response.request.url)
        return Selector(text=self.driver.page_source)

    # This function checks for neglected categories
    def in_neglected_categories(self, category):
        for neglected_cat in NEGLECT_CATEGORIES_LIST:
            if re.search(neglected_cat, category, re.IGNORECASE):
                return True

        return False

    def in_disallowed_keywords(self, url, name, categories):
        categories = ','.join(categories)
        for keyword in DISALLOWED_KEYWORDS:
            if re.search(keyword, url, re.IGNORECASE) or re.search(keyword, name, re.IGNORECASE) or \
                    re.search(keyword, categories, re.IGNORECASE):
                return True
        return False

    def remove_duplicates_using_regex(self, keywords_list):
        finals = []
        for keyword in keywords_list:
            if not re.search(keyword, ' '.join(finals), re.IGNORECASE):
                finals.append(keyword)

        return finals

    def find_keywords_from_str(self, details, keywords):
        finals = []
        details = ' '.join(details)
        for keyword in keywords:
            if re.search(keyword, details, re.IGNORECASE):
                if keyword not in finals:
                    finals.append(keyword)

        return finals

    def convert_price(self, price):
        return "$" + str(
            round(self.currency_converter.convert(int(price.replace("£", "").split(".")[0]), 'GBP', 'USD')))

    def clean_categories(self, categories):
        categories = [cat for cat in categories if not re.search("women", cat, re.IGNORECASE) and
                      not re.search("men", cat, re.IGNORECASE)]
        categories = [cat.split(" ") for cat in categories]
        categories = list(chain.from_iterable(categories))
        categories = [cat for cat in categories if cat != "" and not re.search("Men", cat, re.IGNORECASE) and
                      not re.search("Women", cat, re.IGNORECASE)]
        categories = [cat for cat in categories if cat != ""]
        return self.remove_duplicates_using_regex(categories)

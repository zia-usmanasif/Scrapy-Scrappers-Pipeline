import scrapy
from scrapy.selector import Selector
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import re
import time
import json
from ..items import ThereformationScrapperItem
import os

# Constants
WEBSITE_NAME = "thereformation"
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

DISALLOWED_CATEGORIES = ["shoes", "joggers", "jogger", "heels", "accessories"]
NEGLECT_CATEGORIES_LIST = ['New in', 'Joggers', 'Multipacks', 'new-in',
                           'Socks', 'Exclusives at ASOS', 'Tracksuits & Joggers',
                           "Sportswear", "co-ords", "exclusives", "shoes", "accessories",
                           "heels", "snickers", "earrings", "loafer", "shoes", "joggers", "jogger", "heels", "accessories"]

ALLOWED_CATEGORIES = ['CASUAL', 'SET', 'COVER', 'BACK', 'PANT', 'MINI', 'CORSET', 'TANK', 'COCKTAIL', 'HOMECOMING', 'LINGERIE', 'TOP', 'OVERALL', 'TALL', 'PRINCESS', 'GRAPHIC', 'LEATHER', 'GOING', 'GRADUATION', 'RUSH', 'COLLEGE', 'ULTRA', 'KNIT', 'SHORT', 'FLORAL', 'DENIM', 'LOWER', 'JEANS', 'HOROSCOPE', 'BIKINI',
                      'BLACK', 'FESTIVAL', 'BOTTOM', 'DRESS', 'PANT', 'WHITE', 'NEW', 'FALL', 'LONG', 'MAXI', 'SWEATSHIRT', 'CROP', 'JACKET', 'ROMPER', 'SWIM', 'PINK', 'TUBE', 'CURVE', 'DREAM', 'MIDI', 'LINEN', 'SKIRT', 'CARDIGAN', 'BASIC', 'PETITE', 'LOUNGEWEAR', 'BLAZER', 'ALL', 'BOLERO', 'SHIRT', 'PARTY', 'SWEATER']


class ThereformationSpider(scrapy.Spider):
    name = "thereformation"
    allowed_domains = ["www.thereformation.com"]

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
        url = "https://www.thereformation.com/clothing"
        yield scrapy.Request(url=url, callback=self.parse_product_links)

    def parse_product_links(self, response):
        self.driver.get(response.request.url)
        self.driver.implicitly_wait(2)
        self.scroll_down()
        self.driver.implicitly_wait(2)
        selenium_response = Selector(text=self.driver.page_source)
        product_links = selenium_response.css(
            "div.product-tile a::attr('href')").getall()
        if product_links:
            for link in product_links:
                yield scrapy.Request(url=f"https://www.thereformation.com{link}", callback=self.parse_product)

    def parse_product(self, response):
        url = response.request.url
        product_meta = response.css(
            "script[type='application/ld+json']::text").get()
        if product_meta:
            product_meta = json.loads(product_meta)

        external_id = product_meta.get('sku')
        name = response.css("h1.pdp__name::text").get()
        name = name.strip() if name else ""
        price = response.css("span[data-product-price]::text").get()
        if not price:
            price = product_meta.get('offers').get('price')
        price = price.strip() if price else ""
        sizes = response.xpath(
            "//button[contains(@class, 'anchor--size')] /text()").getall()
        sizes = [item.strip() for item in sizes if item.strip()]
        colors = response.css("button.swatch--color::attr('title')").getall()
        colors = [color.strip() for color in colors if color]
        details = response.css("div.pdp_fit-details-item *::text").getall()
        details = [item.strip()
                   for item in details if item.strip()]
        details = [item for item in details if item != "\n" and item != "."]
        images = response.css(
            "button.product-gallery__button img::attr('cl-data-src')").getall()
        images = [img.strip() for img in images if img]

        fabric = self.find_fabric_from_details(details)
        fit = " ".join(self.find_attr_from_details(
            details, FIT_KEYWORDS))
        neck_line = " ".join(self.find_attr_from_details(
            details, NECK_LINE_KEYWORDS))
        occasions = self.find_attr_from_details(
            details, OCCASIONS_KEYWORDS)
        style = self.find_attr_from_details(details, STYLE_KEYWORDS)
        length = " ".join(self.find_attr_from_details(
            details, LENGTH_KEYWORDS))
        json_data = response.xpath(
            "//script[@type='application/json'][@data-product-json] /text()").extract()
        if json_data:
            json_data = json.loads(json_data[0])

        categories = response.css("ol.breadcrumbs li a::text").getall()
        if len(categories) > 1:
            categories = [categories[1]]
        categories = [cat.strip() for cat in categories if cat]

        meta = {}
        item = ThereformationScrapperItem()
        item["url"] = url
        item["external_id"] = external_id
        item["name"] = name
        item["price"] = price
        item["sizes"] = sizes
        item["categories"] = categories
        item["colors"] = colors
        item["details"] = details
        item["fabric"] = fabric
        item["images"] = images
        item["fit"] = fit
        item["neck_line"] = neck_line
        item["length"] = length
        item["gender"] = "female"
        item["number_of_reviews"] = ""
        item["review_description"] = []
        item["top_best_seller"] = ""
        item["meta"] = meta
        item["occasions"] = occasions
        item["style"] = style
        item["website_name"] = WEBSITE_NAME
        # item["aesthetics"] = aesthetics
        if not self.in_disallowed_categories(url, details, name, categories):
            yield item

    # This helper finds fabric from details and returns it
    def find_fabric_from_details(self, details):
        product_details = ' '.join(details)
        fabrics_founded = re.findall(r"""(\d+ ?%\s?)?(
            velvet\b|silk\b|satin\b|cotton\b|lace\b|
            sheer\b|organza\b|chiffon\b|spandex\b|polyester\b|
            poly\b|linen\b|nylon\b|viscose\b|Georgette\b|Ponte\b|
            smock\b|smocked\b|shirred\b|Rayon\b|Bamboo\b|Knit\b|Crepe\b|
            Leather\b|polyamide\b|Acrylic\b|Elastane\bTencel\bCashmere\b)\)?""", product_details,
                                     flags=re.IGNORECASE | re.MULTILINE)

        fabrics_founded = re.sub("\(|\)", "", ' '.join(
            [''.join(tups) for tups in fabrics_founded]))
        already_founded = []
        if fabrics_founded:
            fabrics_founded = fabrics_founded.split(" ")
            for fabric in fabrics_founded:
                if not re.search(fabric, ' '.join(already_founded), re.IGNORECASE):
                    already_founded.append(fabric)

        return ' '.join(already_founded).strip() if already_founded else ""

    def find_attr_from_details(self, details, keywords):
        details = ' '.join(details)
        ls = []
        for keyword in keywords:
            if re.search(keyword, details, re.IGNORECASE):
                ls.append(keyword)

        return ls

    def in_disallowed_categories(self, url, details, name, categories):
        for keyword in NEGLECT_CATEGORIES_LIST:
            if re.search(keyword, url, re.IGNORECASE) or \
                    re.search(keyword, ' '.join(details), re.IGNORECASE) or \
                    re.search(keyword, name, re.IGNORECASE) or \
                    re.search(keyword, ' '.join(categories), re.IGNORECASE):
                return True
        return False

    def scroll_down(self):
        """A method for scrolling the page."""

        # Get scroll height.
        last_height = self.driver.execute_script(
            "return document.body.scrollHeight")

        while True:

            # Scroll down to the bottom.
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load the page.
            time.sleep(5)

            # Calculate new scroll height and compare with last scroll height.
            new_height = self.driver.execute_script(
                "return document.body.scrollHeight")

            if new_height == last_height:

                break

            last_height = new_height

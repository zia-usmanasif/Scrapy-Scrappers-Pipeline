# Imports
import scrapy
from scrapy import Selector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
from webdriver_manager.chrome import ChromeDriverManager
from ..items import ZaraScrapperItem
import time
import os

# Constants
DISALLOWED_CATEGORIES = ["New", "new-in", "woman-must-have", "SUMMER MUST HAVE",
                         "Accessories", "Beauty", "Perfumes", "Home",
                         "Sale", "Bags", "Bagpacks", "Basics", "ZARA ATELIER",
                         "Trend", "Jogging", "must-have", "Joggers", "TOP SALES", "collection",
                         "woman-basics", "shoes", "bags", "accessories", "woman-beauty-makeup",
                         "woman-beauty-perfumes", "home", "man-basics", "man-bermudas", "man-jogging",
                         "man-shoes", "man-bags", "man-accessories", "man-accessories-perfumes"]

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


class ZaraSpider(scrapy.Spider):
    name = 'zara'
    # this method configures initial settings for selenium chrome webdriver

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
        url = "https://www.zara.com/us/"
        yield scrapy.Request(url=url, callback=self.parse)

    # This function parses categories
    def parse(self, response):
        category_links = response.xpath(
            "//ul[@class='layout-categories-category__subcategory'] /li[@class='layout-categories-category layout-categories-category--level-2'] /a /@href").getall()[:47]
        for link in category_links:
            if not self.in_disallowed_categories(link):
                categories = self.extract_category_name(link)
                yield scrapy.Request(url=link, callback=self.parse_products,
                                     meta={"categories": categories})

    # This function parses products
    def parse_products(self, response):
        products = response.css(
            "li.product-grid-product a::attr('href')").getall()
        for product in products:
            yield scrapy.Request(url=product, callback=self.parse_product,
                                 meta={"categories": response.meta.get("categories")})

    # This function parse product details
    def parse_product(self, response):
        url = response.request.url
        external_id = response.css("html::attr('id')").get()
        if external_id:
            external_id = external_id.split("-")[-1]
        name = response.css("h1.product-detail-info__header-name::text").get()
        price = response.css("span.price-old__amount::text").get()
        if not price:
            price = response.css("span.price-current__amount::text").get()

        colors = response.css(
            "ul.product-detail-color-selector__colors li span.screen-reader-text::text").getall()
        if not colors:
            colors = response.css(
                "p.product-detail-selected-color::text").get()
            colors = [colors.split("|")[0]]

        sizes = response.css(
            "ul.product-detail-size-selector__size-list li span::text").getall()
        sizes = list(set([size.strip()
                     for size in sizes if not re.search(f"-|\s", size)]))
        categories = response.meta.get("categories", [])
        images = response.css(
            "picture.media-image img.media-image__image::attr('src')").getall()
        details = response.css(
            "div.expandable-text__inner-content *::text").getall()
        products_extra_details = self.get_custom_selector(response).css(
            "div.product-detail-extra-detail *::text").getall()
        fabric = self.find_fabric_from_details(
            products_extra_details) if details else ""
        fit = self.find_from_target_string_single(
            products_extra_details, FIT_KEYWORDS)
        neck_line = self.find_from_target_string_single(
            products_extra_details, NECK_LINE_KEYWORDS)
        length = self.find_from_target_string_multiple(
            products_extra_details, name, categories, LENGTH_KEYWORDS)
        gender = categories[0] if categories else ""
        # Extracting Number of reviews
        review_description = []
        number_of_reviews = "0"
        top_best_seller = ""
        occasions = self.find_from_target_multiple_list(
            details, name, categories, OCCASIONS_KEYWORDS)
        style = self.find_from_target_multiple_list(
            details, name, categories, STYLE_KEYWORDS)
        meta = {}
        website_name = "zara"

        item = ZaraScrapperItem()
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
        item["gender"] = gender
        item["number_of_reviews"] = number_of_reviews
        item["review_description"] = review_description
        item["top_best_seller"] = top_best_seller
        item["meta"] = meta
        item["occasions"] = occasions
        item["style"] = style
        item["website_name"] = website_name
        # item["aesthetics"] = aesthetics
        if sizes:
            yield item

    # Helpers

    def in_disallowed_categories(self, category):
        for cat in DISALLOWED_CATEGORIES:
            if re.search(cat.lower(), category, re.IGNORECASE):
                return True
        return False

    def extract_category_name(self, category):
        categories = category.split("/")[-1].split(".")[0].split("-")[:-1]
        for cat in DISALLOWED_CATEGORIES:
            if cat.lower() in categories:
                categories = [c for c in categories if not re.search()]

        return categories

    # This helper finds fabric from details and returns it
    def find_fabric_from_details(self, details):
        product_details = ' '.join(details)
        fabrics_founded = re.findall(r"""(\d+ ?%\s?)(
            velvet\b|silk\b|satin\b|cotton\b|lace\b|
            sheer\b|organza\b|chiffon\b|spandex\b|polyester\b|
            poly\b|linen\b|nylon\b|viscose\b|Georgette\b|Ponte\b|
            smock\b|smocked\b|shirred\b|Rayon\b|Bamboo\b|Knit\b|Crepe\b|
            Leather\b|polyamide\b|Acrylic\b|Elastane\bTencel\bCashmere\b)\)?""", product_details,
                                     flags=re.IGNORECASE | re.MULTILINE)

        return re.sub("\(|\)", "", ' '.join([''.join(tups) for tups in fabrics_founded]))

    def find_from_target_string_single(self, source_data, target_keywords):
        for each_element in source_data:
            if any(keyword.lower() in each_element.lower() for keyword in target_keywords):
                return each_element

        return ""

    def find_from_target_multiple_list(self, details, name, categories, target_keywords):
        target_list = details[:]
        target_list.extend(name)
        target_list.extend(categories)
        final_list = []

        for each_element in target_list:
            if any(keyword.lower() in each_element.lower() for keyword in target_keywords):
                final_list.append(each_element)

        return final_list

    def find_from_target_string_multiple(self, details, name, categories, target_keywords):
        target_list = details[:]
        target_list.extend(name)
        target_list.extend(categories)

        for element in target_list:
            if any(keyword.lower() in element.lower() for keyword in target_keywords):
                return element

        return ""

    def get_custom_selector(self, response):
        self.driver.get(response.request.url)
        return Selector(text=self.driver.page_source)

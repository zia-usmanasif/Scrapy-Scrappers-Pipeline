import scrapy
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re
import json
import signal
import time
from ..items import CuyanaScrapperItem
import os

# Constants
WEBSITE_NAME = "cuyana"
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
                           "heels", "snickers", "earrings"]


class CuyanaSpider(scrapy.Spider):
    name = "cuyana"
    allowed_domains = ["cuyana.com"]

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
        url = "https://cuyana.com/collections/clothing"
        signal.signal(signal.SIGINT, self.handle_interrupt)
        yield scrapy.Request(url=url, callback=self.parse_product_links)

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

    def parse_product_links(self, response):
        self.driver.get(response.request.url)
        self.driver.implicitly_wait(2)
        # First we will scroll down to the bottom of the page
        self.scroll_to_bottom()
        # Then we will get all the product links
        self.driver.implicitly_wait(2)
        product_links = self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.ProductList a")
        product_links = [product.get_attribute(
            'href') for product in product_links]
        if product_links:
            for link in product_links:
                if link:
                    yield scrapy.Request(url=link, callback=self.parse_product)

    def parse_product(self, response):
        url = response.request.url
        name = response.css("h1.ProductMeta__Title::text").get()
        name = name.strip() if name else ""
        price = response.css("span.ProductMeta__Price::text").get()
        price = price.strip() if price else ""
        sizes = response.css("ul.SizeSwatchList li label::text").getall()
        sizes = [item.strip() for item in sizes if item]
        colors = response.css(
            "ul.ColorSwatchList li label span::text").getall()
        colors = [color.strip() for color in colors if color]
        details = response.css("div.ProductMeta__Description *::text").getall()
        details = [item.strip() for item in details if item.strip()]
        images = response.css(
            "div.Product__SlideItem div img::attr('src')").getall()
        images = [img.lstrip('/') for img in images]
        fabric_details = response.css(
            "div.accordion-body ul li::text").getall()
        details_meta = fabric_details + details
        fabric = self.find_fabric_from_details(details_meta)
        fit = " ".join(self.find_attr_from_details(details_meta, FIT_KEYWORDS))
        neck_line = " ".join(self.find_attr_from_details(
            details_meta, NECK_LINE_KEYWORDS))
        occasions = self.find_attr_from_details(
            details_meta, OCCASIONS_KEYWORDS)
        style = self.find_attr_from_details(details_meta, STYLE_KEYWORDS)
        length = " ".join(self.find_attr_from_details(
            details_meta, LENGTH_KEYWORDS))
        reviews = ""
        review_description = []
        script_json_data = response.xpath(
            "//script[@type='application/ld+json'][1] /text()").extract()
        if script_json_data:
            script_json_data = json.loads(script_json_data[0])

        external_id = script_json_data.get('sku')
        categories = [script_json_data.get('category')]
        if not categories:
            categories = self.find_categories_from_details(details_meta)
        if not details:
            details = details_meta
        meta = {}
        item = CuyanaScrapperItem()
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
        item["number_of_reviews"] = reviews.strip() if reviews else ""
        item["review_description"] = review_description
        item["top_best_seller"] = ""
        item["meta"] = meta
        item["occasions"] = occasions
        item["style"] = style
        item["website_name"] = WEBSITE_NAME
        # item["aesthetics"] = aesthetics
        if not self.in_disallowed_categories(url, details, name) and categories:
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

    def remove_duplicates_using_regex(self, keywords_list):
        finals = []
        for keyword in keywords_list:
            if not re.search(keyword, ' '.join(finals), re.IGNORECASE):
                finals.append(keyword)

        return finals

    def in_disallowed_categories(self, url, details, name):
        for keyword in DISALLOWED_CATEGORIES:
            if re.search(keyword, url, re.IGNORECASE) or \
                    re.search(keyword, ' '.join(details), re.IGNORECASE) or \
                    re.search(keyword, name, re.IGNORECASE):
                return True
        return False

    def in_neglected_categories(self, category):
        for neglected_cat in NEGLECT_CATEGORIES_LIST:
            if re.search(neglected_cat, category, re.IGNORECASE):
                return True

        return False

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

    def find_categories_from_details(self, details):
        product_details = ' '.join(details)
        categories_founded = re.findall(r"""(\d+ ?%\s?)?(
            outerwear\b|dress\b|pant\b|legging\b|pants & leggings\b|
            skirt\b|stretch\b|lounge\b|sleepwear\b|sweater\b|
            cape\b|sweater & capes\b|top\b)\)?""", product_details,
                                        flags=re.IGNORECASE | re.MULTILINE)

        categories_founded = re.sub("\(|\)", "", ' '.join(
            [''.join(tups) for tups in categories_founded]))
        already_founded = []
        if categories_founded:
            categories_founded = categories_founded.split(" ")
            for category in categories_founded:
                if not re.search(category, ' '.join(already_founded), re.IGNORECASE):
                    already_founded.append(category)

        return ' '.join(already_founded).strip() if already_founded else ""

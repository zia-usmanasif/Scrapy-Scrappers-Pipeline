import json
import scrapy
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import re
import os
import time
import sys
import signal
from ..items import FarfetchScrapperItem

# Constants
WEBSITE_NAME = "farfetch"
FIT_KEYWORDS = ["Maternity", "Petite", "Plus Size", "Curvy",
                "Tall", "Mid-weight", "High-waisted", "Oversized"]

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
                      "swim", "swimwear", "lounge", "loungewear", "beach"]

LENGTH_KEYWORDS = ["mini", "short", "maxi", "crop", "cropped", "sleeves",
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
CATEGORIES_KEYWORDS = ["dress", "knitwear", "jacket", "dress", "hoodie",
                       "trouser", "pant", "lingerie",
                       "jumpsuit", "beachwear", "pant", "shirt",
                       "activewear", "denim", "coat", "sweatshirt", "bottom",
                       "intimates", "jeans", "sweater", "gown", "jumper", "top",
                       "jumpsuit", "loungewear", "rompers", "cardigan",
                       "skirt", "suit", "dress", "outwear", "blouse", "pants",
                       "shorts", "bottoms", "vest", "dungarees", "T-Shirt",
                       "leggings", "embroidery", "bikini", "blazer", "jersey", "MAXI", "Camisole",
                       "gilet", "cashmere", "shorts", "Trousers", "sleeveless pliss", "two-piece", "Jackets",
                       "padded parka", "hoods", "linen corset", "Midi Dress", "bralette", "swim wear",
                       "logo path windbreaker", "one-piece", "Tunic", "wool", "Parka", "bolero",
                       "jersey", "Abaya", "Kaftan", "shirt", "leggings"]
LINKS_KEYWORDS = ["dress", "knitwear", "jacket", "top", "pant", "lingerie",
                  "jumpsuit", "beachwear", "shirt", "activewear", "denim", "coat", "sweatshirt", "clothes", "innerwear",
                  "wear", "loungewear", "tees", "bottoms", "outwear", ""]

FABRICS_KEYWORDS = ["polyester", "cashmere", "viscose", "Machine wash cold", "metallic", "silk", "rayon", "spandex",
                    "TENCEL", "cotton", "elastane", "lyocell", "LENZING", "LYCRA", "%"]
DISALLOWED_CATEGORIES = ["shoes", "joggers",
                         "heels", "accessories", "cape", "socks"]

base_url = "http://www.farfetch.com/"


class FarfetchSpider(scrapy.Spider):
    name = 'farfetch'
    allowed_domains = ['www.farfetch.com']

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
        url = "https://www.farfetch.com/pk/shopping/women/clothing-1/items.aspx"
        signal.signal(signal.SIGINT, self.handle_interrupt)
        yield scrapy.Request(url=url, callback=self.parse_pages)

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
        for i in range(1, 200):
            url = f"{response.url}?page={i}&view=90&sort=3"
            yield scrapy.Request(url=url, callback=self.parse_products_links)

    def parse_products_links(self, response):
        products_links = response.css(
            "div.ltr-1g1ywla.elu6vcm1 div ul div a::attr('href')").getall()
        for link in products_links:
            url = f"{base_url}{link}"
            yield scrapy.Request(url=url, callback=self.parse_product)

    def parse_product(self, response):
        script_ld_json = response.xpath(
            "//script[@type='application/ld+json']/text()").extract()
        json_data = {}
        if script_ld_json:
            json_data = json.loads(script_ld_json[0])
        external_id = json_data.get("productID")
        name = json_data.get("name")
        price = str(json_data.get('offers')['price'])
        details = [json_data.get('description')]
        details += response.css(
            "div[data-component*='TabPanels'] span ::text").getall()
        details += response.css(
            "div[data-component*='TabPanels'] p ::text").getall()
        details = [detail.strip()
                   for detail in details if detail is not None and detail is not ""]
        fit_meta = response.xpath(
            '//h4[contains(text(), "Fitting information")] /parent::* //text()').getall()
        details_meta = details+fit_meta

        top_best_seller = ""
        colors = response.css("ul._ef6f60 li:nth-child(1)::text").get()
        if colors:
            colors = colors.split("/")
            colors = [color.strip() for color in colors]
        else:
            colors = json_data['color'] if json_data['color'] else []

        number_of_reviews = ''
        fabrics = find_fabric_from_details(details_meta)
        categories = remove_duplicates(
            find_categories(name, response.request.url))
        neck_line = ' '.join(find_data_from_details(
            details_meta, NECK_LINE_KEYWORDS))
        length = ' '.join(find_data_from_details(
            details_meta, LENGTH_KEYWORDS))
        occasions = remove_duplicates(
            find_data_from_details(details_meta, OCCASIONS_KEYWORDS))
        style = remove_duplicates(
            find_data_from_details(details_meta, STYLE_KEYWORDS))
        fit = ' '.join(find_data_from_details(details_meta, FIT_KEYWORDS))
        gender = "women"
        images = []
        for img_obj in json_data['image']:
            images.append(img_obj['contentUrl'])
        sizes = self.extract_sizes(response)

        item = FarfetchScrapperItem()
        url = response.url
        item["external_id"] = external_id
        item["url"] = url
        item["name"] = name
        item["categories"] = categories
        item["price"] = price
        item["colors"] = colors
        item["sizes"] = sizes
        item["fabric"] = fabrics
        item["fit"] = fit
        item["details"] = details
        item["images"] = images
        item["number_of_reviews"] = number_of_reviews
        item["review_description"] = []
        item["top_best_seller"] = top_best_seller
        item["style"] = style
        item["length"] = length
        item["neck_line"] = neck_line
        item["occasions"] = occasions
        item["gender"] = gender
        item["meta"] = {}
        item["website_name"] = WEBSITE_NAME
        if not in_disallowed_categories(name, url, categories) and categories and sizes:
            yield item

    def extract_sizes(self, response):
        try:
            self.driver.get(response.request.url)
            sizes_button = self.driver.find_element(
                By.CSS_SELECTOR, "div[data-component='SizeSelectorLabel']")
            if sizes_button:
                sizes_button.click()
                self.driver.implicitly_wait(5)
                sizes = self.driver.find_elements(
                    By.CSS_SELECTOR, "ul[data-component='SizeSelectorOptions'] li")
                sizes = [size.get_attribute('value') for size in sizes]
                sizes = [size.strip()
                         for size in sizes if size and size != "0"]
                return sizes
        except Exception as e:
            return []

# Helpers


def find_categories(name, url):
    categories = []
    for keyword in CATEGORIES_KEYWORDS:
        if re.search(keyword, name, re.IGNORECASE) or re.search(keyword, url, re.IGNORECASE):
            categories.append(keyword)

    return list(set(categories))


def find_data_from_details(details, keywords):
    ls = []
    details = ' '.join(details)
    for keyword in keywords:
        if re.search(keyword, details, re.IGNORECASE):
            ls.append(keyword)

    return ls


# This helper finds fabric from details and returns it
def find_fabric_from_details(details):
    product_details = ' '.join(details)
    fabrics_founded = re.findall(r"""(\d+ ?%\s?)?(
        velvet\b|silk\b|satin\b|cotton\b|lace\b|
        sheer\b|organza\b|chiffon\b|spandex\b|polyester\b|
        poly\b|linen\b|nylon\b|viscose\b|Georgette\b|Ponte\b|
        smock\b|smocked\b|shirred\b|Rayon\b|Bamboo\b|Knit\b|Crepe\b|
        Leather\b|polyamide\b|Acrylic\b|Elastane\bTencel\bCashmere\b)\)?""", product_details,
                                 flags=re.IGNORECASE | re.MULTILINE)

    return re.sub("\(|\)", "", ' '.join([''.join(tups) for tups in fabrics_founded]))


def in_disallowed_categories(name, url, categories):
    for keyword in DISALLOWED_CATEGORIES:
        if re.search(keyword, name, re.IGNORECASE) or \
            re.search(keyword, url, re.IGNORECASE) or \
                re.search(keyword, ' '.join(categories), re.IGNORECASE):
            return True

    return False


def remove_duplicates(ls):
    return list(set(ls))

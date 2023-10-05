import scrapy
import json
import re
import os
import time
import signal
from scrapy import Selector
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from ..items import HmScrapperItem

# Constants
WEBSITE_NAME = 'hm'

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


class HmSpider(scrapy.Spider):
    name = "hm"
    allowed_domains = ["www2.hm.com"]

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
        url = "https://www2.hm.com/en_us/women/new-arrivals/clothes.html"
        signal.signal(signal.SIGINT, self.handle_interrupt)
        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        total_products = response.css(
            "h2.load-more-heading::attr('data-total')").get()
        PRODUCTS_PER_PAGE = response.css(
            "h2.load-more-heading::attr('data-items-shown')").get()
        PRODUCTS_PER_PAGE = int(PRODUCTS_PER_PAGE) if PRODUCTS_PER_PAGE else 36
        page_size = PRODUCTS_PER_PAGE
        if total_products:
            total_products = int(total_products.strip().replace(",", ""))

        for offset in range(0, total_products, PRODUCTS_PER_PAGE):
            url = f"https://www2.hm.com/en_us/women/new-arrivals/clothes.html?offset={offset}&page-size={page_size}"
            page_size += PRODUCTS_PER_PAGE
            yield scrapy.Request(url=url, callback=self.parse_products)

    def parse_products(self, response):
        product_links = response.css(
            "li.product-item article a.item-link::attr('href')").getall()
        for link in product_links:
            yield scrapy.Request(url=f"https://www2.hm.com{link}", callback=self.parse_product)

    def parse_product(self, response):
        product_meta = response.css("script#product-schema::text").get()
        product_meta = json.loads(product_meta.strip()) if product_meta else {}
        name = product_meta.get("name")
        offers = product_meta.get('offers')
        price = f"${offers[0].get('price')}"
        external_id = product_meta.get('sku')
        details = product_meta.get('description')
        details = details if type(details) == list else [details]
        colors = product_meta.get('color')
        colors = colors if type(colors) == list else [colors]
        fabric = response.xpath(
            "//h3[contains(text(), 'Composition')] /.. /ul /li /p /text()").get()

        self.driver.get(response.url)
        time.sleep(2)
        custom_response = Selector(text=self.driver.page_source)
        categories = custom_response.css(
            "hm-breadcrumbs nav ol  li a::text").getall()
        if categories:
            print("Categorie: ", categories)
            categories = [categories[-2]] if len(
                categories) > 2 else [categories[-1]]
        sizes = custom_response.css("li.js-enable-nib span::text").getall()
        sizes = sizes[1:]
        sizes = [size.strip() for size in sizes if not re.search(
            'notify', size, re.IGNORECASE) or
            not re.search('sold out', size, re.IGNORECASE) or
            not re.search('out of stock', size, re.IGNORECASE) or
            not re.search('few pieces left', size, re.IGNORECASE)]
        images = custom_response.css(
            "figure.pdp-image img::attr('src')").getall()
        images = ['https:'+image for image in images]
        no_reviews = custom_response.css(
            "hm-product-reviews-summary-w-c button span::text").getall()
        if no_reviews:
            no_reviews = re.findall("\d+", no_reviews[-1])
            no_reviews = str(no_reviews[0]) if no_reviews else ""
        details_meta = response.css(
            "hm-product-accordions-w-c *::text").getall()
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

        item = HmScrapperItem()
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
        item["review_description"] = custom_response.xpath(
            "//ul[contains(@class, 'ReviewsList-module')] /li //text()").getall()
        item["top_best_seller"] = ""
        item["meta"] = {}
        item["occasions"] = occasions
        item["style"] = style
        item["website_name"] = WEBSITE_NAME
        if not self.in_disallowed_keywords(response.request.url, name, categories) and colors and sizes and details:
            yield item

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

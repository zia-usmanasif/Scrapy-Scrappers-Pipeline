import scrapy
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import json
import re
from ..items import MadewellScrapperItem
import os
import time
import signal

# Constants
IMAGE_SETTINGS = "?wid=700&hei=889&fmt=jpeg&fit=crop&qlt=75,1&resMode=bisharp&op_usm=0.5,1,5,0"
WEBSITE_NAME = "madewell"
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
                           "heels", "snickers", "earrings", "shoes", "joggers", "jogger", "heels", "accessories"]


class MadewellSpider(scrapy.Spider):
    name = 'madewell'
    allowed_domains = ['www.madewell.com']

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
        url = "https://www.madewell.com/womens/clothing"
        signal.signal(signal.SIGINT, self.handle_interrupt)
        yield scrapy.Request(url=url, callback=self.parse)

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

    def parse(self, response):
        categories = response.xpath(
            '//ul[@aria-labelledby="women-clothing"] /li /a /@href').getall()
        if categories:
            categories = categories[:-1]
        for category in categories:
            yield scrapy.Request(url=category, callback=self.parse_products)

    def parse_products(self, response):
        product_links = response.xpath(
            '//ul[@id="search-result-items"] /li  //a[@class="thumb-link"] /@href').getall()
        if product_links:
            for link in product_links:
                yield scrapy.Request(url=link, callback=self.parse_product)

    def parse_product(self, response):
        details_meta = json.loads(response.css(
            "script#seoProductData::text").get().strip())
        price_meta = json.loads(response.css(
            "input#variantData::attr('value')").get())
        url = response.request.url
        name = "Madewell " + details_meta.get("name")
        external_id = details_meta.get("mpn")
        price = "$" + str(price_meta.get('priceLocal'))
        # details_str = re.sub(f"<i>.*<\/i>", "", ' '.join(details_str))
        details = [details_meta["description"]]
        details = [re.sub(f"<i>.*<\/i>", "", ''.join(details))]
        colors = response.xpath(
            '//ul[@class="swatches color"] /li /a[@class="swatchanchor"] /@title').getall()
        if colors:
            colors = [color.split(":")[-1].strip() for color in colors]
        else:
            colors = [response.css("div.selected-value::text").get().strip()]
        sizes = self.remove_duplicates_using_regex(
            response.css("ul.swatches.size li a::text").getall())
        sizes = [size.strip() for size in sizes]
        categories = details_meta["category"].split(">")
        if categories:
            categories = [cat.strip() for cat in categories]
        categories = [categories[-1]]
        images = details_meta["image"]
        images = [f"{image}{IMAGE_SETTINGS}" for image in images]
        extra_details = response.css(
            "div#accordion__content_details *::text").getall()
        fabric = self.find_fabric_from_details(extra_details)
        fit = response.css("ul.extended-sizing-tiles li a span::text").getall()
        if fit:
            fit = ','.join(fit)
        length = ' '.join(response.css(
            "div.extended-sizing-message::text").getall()).strip()
        neck_line = ' '.join(self.find_attr_from_details(
            extra_details, NECK_LINE_KEYWORDS))
        # response.css("span.BVRRReviewText::text").getall()
        review_description = []
        number_of_reviews = len(
            review_description) if review_description else ""
        top_best_seller = ""
        occasions = self.find_attr_from_details(
            extra_details, OCCASIONS_KEYWORDS)
        style = self.find_attr_from_details(extra_details, STYLE_KEYWORDS)
        meta = {}
        gender = "women"

        item = MadewellScrapperItem()
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
        item["website_name"] = WEBSITE_NAME
        # item["aesthetics"] = aesthetics
        if not self.in_disallowed_categories(url, details, name, categories) and categories:
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
                print("Now checking for: ", fabric,
                      " and already founded are: ", ' '.join(already_founded))
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

    def in_disallowed_categories(self, url, details, name, categories):
        for keyword in NEGLECT_CATEGORIES_LIST:
            if re.search(keyword, url, re.IGNORECASE) or \
                re.search(keyword, ' '.join(details), re.IGNORECASE) or \
                re.search(keyword, name, re.IGNORECASE) or \
                    re.search(keyword, ' '.join(categories), re.IGNORECASE):
                return True
        return False

import scrapy
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import re
import json
from ..items import OhpollyScrapperItem
import os
import time

# Constants
WEBSITE_NAME = "ohpolly"
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
women_clothing_categories = [
    "Dresses",
    "Tops",
    "Bottoms",
    "Outerwear",
    "Activewear",
    "Lingerie",
    "Swimwear",
    "Suits",
    "Sweaters",
    "Blouses",
    "Jeans",
    "Skirts",
    "Pants",
    "Jackets",
    "Coats",
    "Shorts",
    "Leggings",
    "T-shirts",
    "Tank Tops",
    "Cardigans",
    "Hoodies",
    "Vests",
    "Jumpsuits",
    "Rompers",
    "Tunics",
    "Maxi Dresses",
    "Midi Dresses",
    "Mini Dresses",
    "Shift Dresses",
    "Wrap Dresses",
    "Bodycon Dresses",
    "A-line Dresses",
    "Sundresses",
    "Floral Dresses",
    "Party Dresses",
    "Cocktail Dresses",
    "Evening Dresses",
    "Formal Dresses",
    "Wedding Dresses",
    "Bridal Gowns",
    "Bridesmaid Dresses",
    "Maternity Wear",
    "Plus Size Clothing",
    "Petite Clothing",
    "Chinos",
    "Palazzo Pants",
    "Culottes",
    "Cargo Pants",
    "Wide-Leg Pants",
    "Capris",
    "Chino Shorts",
    "Cargo Shorts",
    "Bermuda Shorts",
    "Leather Jackets",
    "Denim Jackets",
    "Bomber Jackets",
    "Parkas",
    "Trench Coats",
    "Pea Coats",
    "Raincoats",
    "Fur Coats",
    "Puffer Jackets",
    "Ponchos",
    "Kimonos",
    "Boleros",
    "Shrugs",
    "Sweatpants",
    "Tennis Skirts",
    "Athletic Shorts",
    "Sports Bras",
    "Yoga Pants",
    "Swimsuits",
    "Bikinis",
    "One-Piece Swimsuits",
    "Tankinis",
    "Cover-Ups",
    "Rash Guards",
    "Bralettes",
    "Corsets",
    "Bustiers",
    "Pantyhose",
    "Stockings",
    "Shapewear",
    "Slips",
    "Camisoles",
    "Bodysuits",
    "Robes",
    "Sleepwear",
    "Pajamas",
    "Nightgowns",
    "Leg Warmers",
]


class OhpollyScrapper(scrapy.Spider):
    name = 'ohpolly'
    allowed_domains = ['www.ohpolly.com']

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
        url = "https://www.ohpolly.com/collections/view-all-clothing"
        yield scrapy.Request(url=url, callback=self.parse_pages)

    def parse_pages(self, response):
        totalItems = response.css('span[data-product-grid-count]::text').get()
        if totalItems:
            totalItems = int(totalItems.strip())
            totalPages = totalItems // 48 + 1
            for page in range(1, totalPages + 1):
                url = f"https://www.ohpolly.com/collections/view-all-clothing?page={page}"
                yield scrapy.Request(url=url, callback=self.parse_product_links)

    def parse_product_links(self, response):
        product_links = response.css(
            "div.clc-ProductGrid_Products li a::attr(href)").getall()
        if product_links:
            for link in product_links:
                if (not self.in_neglected_categories(link)):
                    yield scrapy.Request(url=f"https://www.ohpolly.com{link}", callback=self.parse_product)

    def parse_product(self, response):
        url = response.request.url
        name = response.css("h1.prd-Details_Title::text").get().strip()
        price = response.css("span.prd-Price_Price::text").get().strip()
        sizes = response.css(
            "div.prd-Options_Buttons button span::text").getall()
        sizes = [item.strip() for item in sizes if not re.search(
            r'Notify me when back in stock', item)]
        sizes = [item for item in sizes if item]

        categories = response.css(
            "ul.bdc-Breadcrumb_Items li.bdc-Breadcrumb_Item span::text").getall()
        colors = response.css(
            "div.prd-Colors_Colors a span.util-ScreenReaderOnly::text").getall()
        colors = [color.strip() for color in colors if color]
        details = response.css("div.prd-Accordion_Body * ::text").getall()
        details = [item.strip() for item in details if item.strip()
                   != "" and "Notify me when back in stock" not in item]
        categories = self.clean_categories(
            categories, name + url + ' '.join(details))
        images = response.css(
            "button.prd-Media_Thumbnail div img::attr('src')").getall()
        images = [img.lstrip('/') for img in images]
        fabric = self.find_fabric_from_details(details)
        fit = " ".join(self.find_attr_from_details(details, FIT_KEYWORDS))
        neck_line = " ".join(self.find_attr_from_details(
            details, NECK_LINE_KEYWORDS))
        occasions = self.find_attr_from_details(details, OCCASIONS_KEYWORDS)
        style = self.find_attr_from_details(details, STYLE_KEYWORDS)
        length = " ".join(self.find_attr_from_details(
            details, LENGTH_KEYWORDS))
        reviews = response.css("span.oke-w-navBar-item-count::text").get()
        review_description = response.css(
            "ul.oke-w-reviews-masonryGrid li *::text").getall()

        product_meta = response.xpath(
            "//script[@type='application/ld+json'] /text()").get()
        if product_meta:
            product_meta = json.loads(product_meta)

        external_id = product_meta.get('mpn')
        meta = {}
        item = OhpollyScrapperItem()
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
        item["number_of_reviews"] = reviews.strip() if reviews else "0"
        item["review_description"] = review_description
        item["top_best_seller"] = ""
        item["meta"] = meta
        item["occasions"] = occasions
        item["style"] = style
        item["website_name"] = WEBSITE_NAME

        # item["aesthetics"] = aesthetics
        if not self.in_disallowed_categories(url, details, name, categories) and categories:
            yield item

    def clean_categories(self, categories, details):
        cats_len = len(categories)
        final_categories = []
        for keyword in women_clothing_categories:
            if (re.search(keyword, details, re.IGNORECASE)):
                final_categories.append(keyword)

        if (cats_len == 2):
            final_categories.append(categories[-1])
        else:
            if re.search('back to basics', ' '.join(categories), re.IGNORECASE):
                final_categories.append(categories[cats_len - 3])
            else:
                final_categories.append(categories[cats_len - 2])
        return final_categories

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

    def in_neglected_categories(self, category):
        for neglected_cat in NEGLECT_CATEGORIES_LIST:
            if re.search(neglected_cat, category, re.IGNORECASE):
                return True

        return False

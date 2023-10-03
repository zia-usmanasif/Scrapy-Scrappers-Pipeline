import scrapy
from scrapy.selector import Selector
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import re
import json
import os
import time
from ..items import PrincesspollyScrapperItem


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


NEGLECT_CATEGORIES_LIST = ['New in', 'Joggers', 'Multipacks', 'new-in',
                           'Socks', 'Exclusives at ASOS', 'Tracksuits & Joggers',
                           "Sportswear", "co-ords", "exclusives", "shoes", "accessories",
                           "heels", "snickers", "earrings", "shoes", "joggers", "jogger", "heels", "accessories"]

ALLOWED_CATEGORIES = ['CASUAL', 'SET', 'COVER', 'BACK', 'PANT', 'MINI', 'CORSET', 'TANK', 'COCKTAIL', 'HOMECOMING', 'LINGERIE', 'TOP', 'OVERALL', 'TALL', 'PRINCESS', 'GRAPHIC', 'LEATHER', 'GOING', 'GRADUATION', 'RUSH', 'COLLEGE', 'ULTRA', 'KNIT', 'SHORT', 'FLORAL', 'DENIM', 'LOWER', 'JEANS', 'HOROSCOPE', 'BIKINI',
                      'BLACK', 'FESTIVAL', 'BOTTOM', 'DRESS', 'PANT', 'WHITE', 'NEW', 'FALL', 'LONG', 'MAXI', 'SWEATSHIRT', 'CROP', 'JACKET', 'ROMPER', 'SWIM', 'PINK', 'TUBE', 'CURVE', 'DREAM', 'MIDI', 'LINEN', 'SKIRT', 'CARDIGAN', 'BASIC', 'PETITE', 'LOUNGEWEAR', 'BLAZER', 'ALL', 'BOLERO', 'SHIRT', 'PARTY', 'SWEATER']


class PrincesspollySpider(scrapy.Spider):
    name = "princesspolly"
    allowed_domains = ["us.princesspolly.com"]

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
        url = "https://us.princesspolly.com/collections/clothing"
        yield scrapy.Request(url=url, callback=self.parse_products_by_pages)

    def parse_products_by_pages(self, response):

        # Now extract product pages
        total_products = response.css(
            "div.paginate__viewed strong:nth-child(2)::text").get()
        if total_products:
            total_products = int(total_products.replace(",", "").strip())
            totalPages = total_products // 48 + 1

            for page in range(1, totalPages + 1):
                yield scrapy.Request(url=f"{response.request.url}?page={page}", callback=self.parse_product_links)

    def parse_product_links(self, response):
        product_links = response.css(
            "div.product-tile__images a::attr('href')").getall()
        if product_links:
            for link in product_links:
                yield scrapy.Request(url=f"https://us.princesspolly.com{link}", callback=self.parse_product)

    def parse_product(self, response):
        url = response.request.url
        external_id = response.css(
            "meta[itemprop='sku']::attr('content')").get()
        name = response.css("h1.product__title::text").get()
        name = name.strip() if name else ""
        price = response.css("span[data-product-price]::text").get()
        price = price.strip() if price else ""
        sizes = response.css(
            "ul.product__select-sizes-list li button::text").getall()
        sizes = [item.strip() for item in sizes if item.strip()]
        colors = response.css(
            "div.product__swatches a::attr('data-product-variant-color')").getall()
        colors = [color.strip() for color in colors if color]
        details = response.css(
            "div.product-details__content ul li::text").getall()
        details = [item.strip() for item in details if item.strip()]
        images = response.css(
            "div.swiper-slide picture img::attr('src')").getall()
        images = [re.sub(r'width=\d+', 'width=1000', img.lstrip('/'))
                  for img in images if "width" in img]

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

        categories = [json_data.get('type')]
        if not categories:
            categories = self.find_categories(
                details+[name+" "+url], ALLOWED_CATEGORIES)
        meta = {}
        item = PrincesspollyScrapperItem()
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

    def scroll_till_element(self, path, is_css_selector=True):

        element_locator = (
            By.CSS_SELECTOR, path) if is_css_selector else self.driver.find_element(By.XPATH, path)

        max_scrolls = 10
        scroll_count = 0
        while scroll_count < max_scrolls:
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(element_locator))
                break
            except:
                pass

            scroll_count += 1

    def find_categories(self, product_details, keywords):
        # Create a regex pattern based on the provided keywords
        keywords = [self.inflect_engine.singular_noun(
            keyword.split(" ")[0]) for keyword in keywords]
        keywords = [keyword for keyword in keywords if keyword is not False and type(
            keyword) is str]

        keywords_pattern = '|'.join(keywords)
        regex_pattern = r"(\d+ ?%?\s?)?(" + keywords_pattern + r"\b)\)?"

        # Use the generated regex pattern to find categories
        categories_founded = re.findall(
            regex_pattern, ' '.join(product_details), flags=re.IGNORECASE | re.MULTILINE)

        categories_list = [category[1]
                           for category in categories_founded if category[1]]
        # Eliminate duplicate entries by converting to set and back to list
        categories_founded = list(set(categories_list))

        return categories_founded

    def extract_reviews(self):
        self.driver.implicitly_wait(2)
        self.scroll_till_element('span.yotpo-filter-stars')
        self.driver.implicitly_wait(2)
        selenium_response = Selector(text=self.driver.page_source)
        no_reviews = selenium_response.css('span.reviews-qa-label::text').get()
        review_titles = selenium_response.css(
            'div.yotpo-main  div.content-title::text').getall()
        review_descriptions = selenium_response.css(
            'div.yotpo-main  div.yotpo-review-wrapper div.content-review::text').getall()

        reviews = [review_titles[i]+review_descriptions[i]
                   for i in range(len(review_titles))]

        return no_reviews, reviews

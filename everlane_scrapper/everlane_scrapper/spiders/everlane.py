import scrapy
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
import os
import time
import signal
from ..items import EverlaneScrapperItem

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

ALLOWED_CATEGORIES = ['CASUAL', 'SET', 'COVER', 'BACK', 'PANT', 'MINI', 'CORSET', 'TANK', 'COCKTAIL', 'HOMECOMING', 'LINGERIE', 'TOP', 'OVERALL', 'TALL', 'PRINCESS', 'GRAPHIC', 'LEATHER', 'GOING', 'GRADUATION', 'RUSH', 'COLLEGE', 'ULTRA', 'KNIT', 'SHORT', 'FLORAL', 'DENIM', 'LOWER', 'JEANS', 'HOROSCOPE', 'BIKINI',
                      'BLACK', 'FESTIVAL', 'BOTTOM', 'DRESS', 'PANT', 'WHITE', 'NEW', 'FALL', 'LONG', 'MAXI', 'SWEATSHIRT', 'CROP', 'JACKET', 'ROMPER', 'SWIM', 'PINK', 'TUBE', 'CURVE', 'DREAM', 'MIDI', 'LINEN', 'SKIRT', 'CARDIGAN', 'BASIC', 'PETITE', 'LOUNGEWEAR', 'BLAZER', 'ALL', 'BOLERO', 'SHIRT', 'PARTY', 'SWEATER']


class EverlaneSpider(scrapy.Spider):
    name = "everlane"
    allowed_domains = ["www.everlane.com"]
    start_urls = ["https://www.everlane.com/collections/everlane-editions"]

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

    def parse(self, response):
        self.driver.get(response.request.url)
        self.driver.implicitly_wait(5)
        self.scroll_to_bottom()
        selenium_response = Selector(text=self.driver.page_source)
        product_links = selenium_response.css(
            "a.styles_product-details__name__7gBXp::attr(href)").getall()
        print("product links: ", product_links)
        print("total scrapped: ", len(product_links))

    def scroll_to_bottom(self):
        """A method for scrolling the page."""

        # Get scroll height.
        last_height = self.driver.execute_script(
            "return document.body.scrollHeight")

        while True:

            # Scroll down to the bottom.
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight-500);")

            # Wait to load the page.
            time.sleep(10)

            # Calculate new scroll height and compare with last scroll height.
            new_height = self.driver.execute_script(
                "return document.body.scrollHeight")

            if new_height == last_height:
                break

            last_height = new_height

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

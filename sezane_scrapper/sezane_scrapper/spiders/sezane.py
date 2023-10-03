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
from ..items import SezaneScrapperItem
import os
import signal
import time  # 102.0.5005.115
WEBSITE_NAME = 'sezane'
my_dict = {
    "Tops": ["Coats & Jackets", "Co-ords", "Hoodies & Sweatshirts", "Tops", "Sweaters & Cardigans"],
    "Bottoms": ["Bottoms", "Denim"],
    "Dresses": ["Dresses", "Lingerie & Sleepwear", "Jumpsuits & Rompers", "Loungewear", "Swimwear & Beachwear"]
}
FIT_KEYWORDS = ["Maternity", "Petite", "Plus Size", "Curvy", "Tall"]
NECK_LINE_KEYWORDS = [
    "Scoop",
    "Round Neck," "U Neck",
    "U-Neck",
    "V Neck",
    "V-neck",
    "V Shape",
    "V-Shape",
    "Deep",
    "Plunge",
    "Square",
    "Straight",
    "Sweetheart",
    "Princess",
    "Dipped",
    "Surplice",
    "Halter",
    "Asymetric",
    "One-Shoulder",
    "One Shoulder",
    "Turtle",
    "Boat",
    "Off- Shoulder",
    "Collared",
    "Cowl",
    "Neckline",
]


FABRIC_NAMES = [
    "Viscose",
    "All Weather",
    "Arcylic",
    "Bast Fibres",
    "Canvas",
    "Cashmere",
    "Chiffon",
    "Cool Max",
    "Corduroy",
    "Cotton",
    "Crepe",
    "Crochet",
    "Denim",
    "Down",
    "Eyelet",
    "Faux Fur",
    "Fleece",
    "French Terry",
    "Jersey",
    "Knit",
    "Lace",
    "Leather",
    "Linen",
    "Mesh",
    "Modal",
    "Nylon",
    "Other",
    "Performance",
    "Poly Blend",
    "Polyester",
    "Rayon",
    "Satin",
    "Scuba",
    "Sequin" "Sherpa",
    "Silk",
    "Spandex",
    "Suede",
    "Synthetic",
    "Tencel",
    "Tweed",
    "Twill",
    "Velour",
    "Velvet",
    "Wool",
]

OCCASIONS_KEYWORDS = [
    "office",
    "work",
    "smart",
    "workwear",
    "wedding",
    "nuptials",
    "night out",
    "evening",
    "spring",
    "summer",
    "day",
    "weekend",
    "outdoor",
    "outdoors",
    "adventure",
    "black tie",
    "gown",
    "formal",
    "cocktail",
    "date night",
    "vacation",
    "vacay",
    "fit",
    "fitness",
    "athletics",
    "athleisure",
    "work out",
    "sweat",
    "swim",
    "swimwear",
    "lounge",
    "loungewear",
]

LENGTH_KEYWORDS = [
    "length",
    "mini",
    "short",
    "maxi",
    "crop",
    "cropped",
    "sleeves",
    "tank",
    "top",
    "three quarter",
    "ankle",
    "long",
]

STYLE_KEYWORDS = [
    "bohemian",
    "embellished",
    "sequin",
    "floral",
    "off shoulder",
    "puff sleeve",
    "bodysuit",
    "shell",
    "crop",
    "corset",
    "tunic",
    "bra",
    "camisole",
    "polo",
    "aviator",
    "shearling",
    "sherpa",
    "biker",
    "bomber",
    "harrington",
    "denim",
    "jean",
    "leather",
    "military",
    "quilted",
    "rain",
    "tuxedo",
    "windbreaker",
    "utility",
    "duster",
    "faux fur",
    "overcoat",
    "parkas",
    "peacoat",
    "puffer",
    "skater",
    "trench",
    "Fleece",
    "a line",
    "bodycon",
    "fitted",
    "high waist",
    "high-low",
    "pencil",
    "pleat",
    "slip",
    "tulle",
    "wrap",
    "cargo",
    "chino",
    "skort",
    "cigarette",
    "culottes",
    "flare",
    "harem",
    "relaxed",
    "skinny",
    "slim",
    "straight leg",
    "tapered",
    "wide leg",
    "palazzo",
    "stirrup",
    "bootcut",
    "boyfriend",
    "loose",
    "mom",
    "jeggings",
    "backless",
    "bandage",
    "bandeau",
    "bardot",
    "one-shoulder",
    "slinger",
    "shift",
    "t-shirt",
    "smock",
    "sweater",
    "gown",
]

AESTHETIC_KEYWORDS = [
    "E-girl",
    "VSCO girl",
    "Soft Girl",
    "Grunge",
    "CottageCore",
    "Normcore",
    "Light Academia",
    "Dark Academia ",
    "Art Collective",
    "Baddie",
    "WFH",
    "Black",
    "fishnet",
    "leather",
]

GENDERS = ["women", "men"]

IGNORE = [' ', '\n']

CATEGORIES = {
    "women": {
        "Denim": "https://sezane.com/us/collection/denim?displayMode=column",
        "Dresses": "https://sezane.com/us/collection/dresses?displayMode=column",
        "Jackets": "https://sezane.com/us/collection/jackets-trench-coats?displayMode=column",
        "Jumpsuits": "https://sezane.com/us/collection/bottoms/jumpsuits?displayMode=column",
        "Knitwear": "https://sezane.com/us/collection/the-knitwear-gallery?displayMode=column",
        "Marinieres & Sweatshirts": "https://sezane.com/us/collection/t-shirts/sweat-shirts?displayMode=column",
        "Skirts & Shorts": "https://sezane.com/us/collection/skirts-shorts?displayMode=column",
        "Swimwear": "https://sezane.com/us/collection/swimwear?displayMode=column",
        "T-Shirts": "https://sezane.com/us/collection/t-shirts?displayMode=column",
        "Tops": "https://sezane.com/us/collection/Tops?displayMode=column",
        "Trousers": "https://sezane.com/us/collection/bottoms/trousers?displayMode=column",
    },
}

CATEGORY_KEYWORDS = ['Bottom', 'Shift', 'Swim Brief', 'Quilted', 'Boyfriend',
                     'Padded', 'Track', 'Other', 'Oversized', 'Denim Skirt',
                     'Stick On Bra', 'Cardigan', 'Thong', 'Romper', 'Pea Coat',
                     'Skater', 'Swing', 'Lingerie & Sleepwear', 'Wrap', 'Cargo Pant',
                     'Cape', 'Trucker', 'Nursing', 'Bikini', 'Parka', 'Regular', 'Denim',
                     'Duster', 'Faux Fur', 'Hoodie', 'Bralet', 'Overcoat', 'Corset Top',
                     'T-Shirt', 'Mini', 'Maxi', 'Blazer', 'Super Skinny', 'Summer Dresses',
                     'Chino', 'Short', 'Set', 'Military', 'Overall', 'Vest', 'Bomber Jacket',
                     'Tea', 'Ski Suit', 'Work Dresses', 'High Waisted', 'Culotte', 'Overall Dress',
                     'Jean', 'Loungewear', 'Leather Jacket', 'Unpadded', 'Coats & Jackets', 'Underwired',
                     'Corset', 'Night gown', 'Poncho', 'Pant', 'Cigarette', 'Sweatpant', 'Rain Jacket',
                     'Loose', 'Swimwear & Beachwear', 'Shirt', 'Denim Jacket', 'Co-ord', 'Tight', 'Vacation Dress',
                     'Harrington', 'Bandage', 'Bootcut', 'Biker', 'Crop Top', 'Trench', 'Tracksuit', 'Suit Pant',
                     'Relaxed', 'Day Dresses', 'Tuxedo', 'Tapered', 'Wide Leg', 'Bohemian', 'Pleated', 'Wiggle',
                     'One Shoulder', 'Smock Dress', 'Flare', 'Peg Leg', 'Cover Up', 'Unitard', 'Sweater',
                     'Lounge', 'Top', 'Bodycon', 'Push Up', 'Slip', 'Knitwear', 'Leather', 'Pencil Dress',
                     'Off Shoulder', 'Jersey Short', 'Multiway', 'Balconette', 'Wax Jacket', 'Coat', 'Brief',
                     'Coach', 'Jumpsuits & Rompers', 'Bra', 'Long Sleeve', 'Fleece', 'Activewear', 'Jegging',
                     'Outerwear', 'Bandeau', 'Slim', 'Going Out Dresses', 'Bardot', 'Pajama', 'Sweatsuit',
                     'Blouse', 'Sweaters & Cardigans', 'Straight Leg', 'Windbreaker', 'Tank Top', 'Cold Shoulder',
                     'Halter', 'Dresses', 'T-Shirt', 'Trouser', 'Cami', 'Camis', 'Wedding Guest', 'Bodysuit', 'Triangle',
                     'Casual Dresses', 'Chino Short', 'Boiler Suit', 'Raincoat', 'Formal Dresses', 'Skinny',
                     'Jumper', 'Strapless', 'Cropped', 'Jacket', 'Bridesmaids Dress', 'Tunic', 'A Line',
                     'Denim Dress', 'Cocktail', 'Skirt', 'Jumpsuit', 'Shapewear', 'Occasion Dresses',
                     'Hoodies & Sweatshirts', 'Sweatshirt', 'Aviator', 'Sweater Dress', 'Sports Short',
                     'Shirt', 'Puffer', 'Cargo Short', 'Tulle', 'Swimsuit', 'Mom Jean', 'Legging',
                     'Plunge', 'Teddie', 'Denim Short', 'Intimate', 'Pencil Skirt', 'Backless', 'Tank']

CATEGORY_TO_TYPE = {
    'Co-ords': ['Co-ord', 'Sweatsuit', 'Tracksuit', 'Set'],
    'Coats & Jackets': ['Coats & Jacket', 'Cape', 'Cardigan', 'Coat', 'Jacket', 'Poncho', 'Ski Suit', 'Vest', 'Blazer'],
    'Dresses': ['Dresses', 'Bridesmaids Dress', 'Casual Dress', 'Going Out Dress', 'Occasion Dress',
                'Summer Dress', 'Work Dress', 'Formal Dress', 'Day Dress', 'Wedding Guest', 'Vacation Dress'],
    'Hoodies & Sweatshirts': ['Hoodies & Sweatshirts', 'Fleece', 'Hoodie', 'Sweatshirt'],
    'Denim': ['Denim Jacket', 'Denim Dress', 'Denim Skirt', 'Denim Short', 'Jean', 'Jegging'],
    'Jumpsuits & Rompers': ['Jumpsuits & Rompers', 'Boiler Suit', 'Jumpsuit', 'Overall', 'Romper', 'Unitard'],
    'Lingerie & Sleepwear': ['Lingerie & Sleepwear', 'Intimate', 'Bra', 'Brief', 'Corset', 'Bralet', 'Night gown',
                             'Pajama', 'Shapewear', 'Slip', 'Teddie', 'Thong', 'Tight', 'Bodysuit', 'Camis', 'Cami'],
    'Loungewear': ['Loungewear', 'Lounge', 'Activewear', 'Outerwear', 'Hoodie', 'Legging', 'Overall', 'Pajama',
                   'Sweatpant', 'Sweatshirt', 'Tracksuit', 'T-Shirt'],
    'Bottoms': ['Bottom', 'Chino', 'Legging', 'Pant', 'Suit Pant', 'Sweatpant', 'Tracksuit', 'Short', 'Skirt',
                'Trouser'],
    'Sweaters & Cardigans': ['Sweaters & Cardigans', 'Sweatpant', 'Cardigan', 'Sweater', 'Knitwear'],
    'Swimwear & Beachwear': ['Swimwear & Beachwear', 'Bikini', 'Cover Up', 'Short', 'Skirt', 'Swim Brief', 'Swimsuit'],
    'Tops': ['Top', 'Blouse', 'Bodysuit', 'Bralet', 'Camis', 'Corset Top', 'Crop Top', 'Shirt', 'Sweater',
             'Tank Top', 'T-Shirt', 'Tunic'],
}
CATEGORY_TO_STYLE = {
    'Co-ords': ['Co-ords'],
    'Coats & Jackets': ['Coats & Jackets', 'Aviator', 'Biker', 'Bomber Jacket', 'Coach', 'Denim Jacket', 'Duster', 'Faux Fur', 'Harrington', 'Leather', 'Leather Jacket', 'Military', 'Other', 'Overcoat', 'Parkas', 'Pea Coat', 'Puffer', 'Quilted', 'Raincoats', 'Rain Jackets', 'Regular', 'Skater', 'Track', 'Trench', 'Trucker', 'Tuxedo', 'Wax Jacket', 'Windbreaker'],
    'Dresses': ['Dresses', 'A Line', 'Backless', 'Bandage', 'Bandeau', 'Bardot', 'Bodycon', 'Bohemian', 'Cold Shoulder', 'Denim', 'Jumper', 'Leather', 'Long Sleeve', 'Off Shoulder', 'One Shoulder', 'Other', 'Overall Dress', 'Pencil Dress', 'Shift', 'Shirt', 'Skater', 'Slip', 'Smock Dresses', 'Sweater Dress', 'Swing', 'Tea', 'T-Shirt', 'Wiggle', 'Wrap', 'Cocktail', 'Maxi', 'Mini'],
    'Hoodies & Sweatshirts': ['Hoodies & Sweatshirts'],
    'Denim': ['Jeans', 'Bootcut', 'Boyfriend', 'Cropped', 'Flare', 'High Waisted', 'Loose', 'Mom Jeans', 'Other', 'Regular', 'Skinny', 'Slim', 'Straight Leg', 'Super Skinny', 'Tapered', 'Wide Leg'],
    'Jumpsuits & Rompers': ['Jumpsuits & Rompers'],
    'Lingerie & Sleepwear': ['Lingerie & Sleepwear', 'Balconette', 'Halter', 'Multiway', 'Nursing', 'Padded', 'Plunge', 'Push Up', 'Stick On Bra', 'Strapless', 'Triangle', 'T-Shirt', 'Underwired', 'Unpadded'],
    'Loungewear': ['Loungewear'],
    'Bottoms': ['Bottoms', 'Cargo Pants', 'Cigarette', 'Cropped', 'Culottes', 'Flare', 'High Waisted', 'Other', 'Oversized', 'Peg Leg', 'Regular', 'Relaxed', 'Skinny', 'Slim', 'Straight Leg', 'Super Skinny', 'Tapered', 'Wide Leg', 'Cargo Shorts', 'Chino Shorts', 'Denim', 'High Waisted', 'Jersey Shorts', 'Other', 'Oversized', 'Regular', 'Relaxed', 'Skinny', 'Slim', 'Sports Shorts', 'A Line', 'Bodycon', 'Denim', 'High Waisted', 'Other', 'Pencil Skirt', 'Pleated', 'Skater', 'Slip', 'Tulle', 'Wrap'],
    'Sweaters & Cardigans': ['Sweaters & Cardigans'],
    'Swimwear & Beachwear': ['Swimwear & Beachwear', 'Halter', 'High Waisted', 'Multiway', 'Padded', 'Plunge', 'Strapless', 'Triangle', 'Underwired'],
    'Tops': ['Tops'],
}


class SEZANE(scrapy.Spider):
    name = "sezane"

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
        self.first = True
        super().__init__(*a, **kw)

    def start_requests(self):
        url = "https://sezane.com/us"
        signal.signal(signal.SIGINT, self.handle_interrupt)
        yield scrapy.Request(url, callback=self.parse, dont_filter=True)

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
        for gender in CATEGORIES:
            for category in CATEGORIES[gender]:
                yield scrapy.Request(
                    url=CATEGORIES[gender][category],
                    callback=self.parse_category,
                    dont_filter=True,
                    meta={"gender": gender, "category": category},
                    priority=1,
                )

    def is_first(self):
        if self.first:
            self.first = False
            time.sleep(5)
            try:  # Close Cookies
                self.driver.find_element(
                    by=By.CSS_SELECTOR, value="button[class='onetrust-close-btn-handler banner-close-button ot-close-link']").click()
            except Exception as e:
                print("********Error in closing cookies: ", e)
            time.sleep(1)

            try:
                self.driver.find_element(
                    by=By.CSS_SELECTOR, value="button[id='dropdown-trigger-country-name']").click()
                time.sleep(1)
                self.driver.find_element(
                    by=By.CSS_SELECTOR, value="ul[id='dropdown-country-name']").find_elements(by=By.TAG_NAME, value="li")[1].click()
                self.driver.find_element(
                    by=By.CSS_SELECTOR, value="button[id='select-country-submit']").click()
            except Exception as e:
                print("********Error in closing country select: ", e)

            time.sleep(3)

    def parse_category(self, response):

        gender = response.meta.get("gender")
        category = response.meta.get("category")
        self.driver.get(response.url)
        self.driver.implicitly_wait(5)
        time.sleep(2)

        self.is_first()
        counter = 0
        last_s_height = self.driver.execute_script("return window.pageYOffset")
        while True:
            height = self.driver.execute_script(
                "return document.body.scrollHeight")
            self.driver.execute_script(f"window.scrollTo(0, {height-1000});")
            time.sleep(2)
            new_s_height = self.driver.execute_script(
                "return window.pageYOffset")
            print(last_s_height, new_s_height)
            if last_s_height == new_s_height:
                counter += 1
            else:
                counter = 0

            if counter > 1:
                break

            last_s_height = new_s_height

        products_links = [product.get_attribute('href') for product in self.driver.find_elements(
            by=By.CSS_SELECTOR, value="a[class='c-link c-link--inbl c-link--tertiary c-link--start']")]
        for url in products_links:
            for i in range(3):
                try:
                    self.driver.get(url)
                    info_elem = self.driver.find_element(
                        by=By.CSS_SELECTOR, value="div[class='o-container u-mt-sm-bis@md-plus u-mt-sm-bis@md js-product-content']")
                    external_id = self.driver.find_element(
                        by=By.CSS_SELECTOR, value="article[class='o-grid__col o-grid__col--9 o-grid__col--offset-1 o-grid__col--22@sm u-flex@sm u-flex-column@sm c-product'").get_attribute('data-product-hash')
                    name = info_elem.find_element(
                        by=By.CSS_SELECTOR, value="h1[class='js-sticky-trigger u-h3 u-inline u-align-middle c-product__title']").text

                    try:
                        price = info_elem.find_element(by=By.CSS_SELECTOR, value="div[class='u-text-lg u-text-secondary c-product__price']").find_element(
                            by=By.TAG_NAME, value="s").get_attribute('textContent').replace("\n", '').strip()
                    except:
                        price = info_elem.find_element(
                            by=By.CSS_SELECTOR, value="div[class='u-text-lg u-text-secondary c-product__price']").get_attribute('textContent').replace("\n", '').strip()

                    size = [elem.text for elem in info_elem.find_elements(
                        by=By.CSS_SELECTOR, value="label[class*='c-size']")]
                    sizes = []
                    for i in size:
                        if "xxxl" == i.lower():
                            sizes.append("3X")
                            continue
                        if "xxl" == i.lower():
                            sizes.append("2X")
                            continue
                        if "xxs" == i.lower():
                            sizes.append("XXS")
                            continue
                        if "xx" == i.lower():
                            sizes.append("XX")
                            continue
                        if "25" == i.lower():
                            sizes.append("25")
                            continue
                        if "00" == i.lower():
                            sizes.append("00")
                            continue
                        if "0" == i.lower():
                            sizes.append("00")
                            continue
                        if "26" == i.lower():
                            sizes.append("26")
                            continue
                        if "34" == i.lower():
                            sizes.append("34")
                            continue
                        if "8" == i.lower():
                            sizes.append("08")
                            continue
                        if "30" == i.lower():
                            sizes.append("30")
                            continue
                        if "32" == i.lower():
                            sizes.append("32")
                            continue
                        if "12" == i.lower():
                            sizes.append("12")
                            continue
                        if "6" == i.lower():
                            sizes.append("06")
                            continue
                        if "10" == i.lower():
                            sizes.append("10")
                            continue
                        if "28" == i.lower():
                            sizes.append("28")
                            continue
                        if "2" == i.lower():
                            sizes.append("02")
                            continue
                        if "38" == i.lower():
                            sizes.append("38")
                            continue
                        if "4" == i.lower():
                            sizes.append("04")
                            continue
                        if "36" == i.lower():
                            sizes.append("36")
                            continue
                        if "14" == i.lower():
                            sizes.append("14")
                            continue
                        if "xl" == i.lower():
                            sizes.append("XL")
                            continue
                        if "xs" == i.lower():
                            sizes.append("XS")
                            continue
                        if "1x" == i.lower():
                            sizes.append("XL")
                            continue
                        if "2x" == i.lower():
                            sizes.append("2X")
                            continue
                        if "3x" == i.lower():
                            sizes.append("3X")
                            continue
                        if "s" == i.lower():
                            sizes.append("S")
                            continue
                        if "m" == i.lower():
                            sizes.append("M")
                            continue
                        if "l" == i.lower():
                            sizes.append("L")
                            continue
                    sizes = list(set(sizes))
                    colors = [elem.get_attribute('textContent').replace("\n", "").strip() for elem in self.driver.find_element(by=By.CSS_SELECTOR, value="form[action='/us/cart/product']").find_element(
                        by=By.CSS_SELECTOR, value="div[class='o-grid__col']").find_elements(by=By.CSS_SELECTOR, value="span[class*='c-switch__text']")]
                    description = [elem.text.replace("\n", "").strip() for elem in info_elem.find_element(
                        by=By.CSS_SELECTOR, value="div[id='tab-panel-product-desc']").find_elements(by=By.TAG_NAME, value="li")]
                    f_details = [sub_elem.strip() for elem in info_elem.find_element(by=By.CSS_SELECTOR, value="div[id='tab-panel-product-details']").find_elements(
                        by=By.TAG_NAME, value="p") for sub_elem in elem.get_attribute("textContent").split("\n")]
                    details = description + f_details

                    new_details = []
                    for detail in details:
                        if detail != "":
                            new_details.append(detail)
                    details = new_details
                    images = [elem.get_attribute('src') for elem in self.driver.find_elements(
                        by=By.CSS_SELECTOR, value="img[class='swiper-lazy u-w-100 swiper-lazy-loaded']")]

                    item = SezaneScrapperItem()
                    item["external_id"] = external_id
                    item["url"] = url
                    item["name"] = name
                    categories = []
                    scrapped_categories = [category]
                    extracted_categories = extract_categories_from(url)
                    if extracted_categories:
                        categories = find_actual_parent(
                            scrapped_categories, extracted_categories)
                    else:
                        extracted_categories = extract_categories_from(name)
                        if extracted_categories:
                            categories = find_actual_parent(
                                scrapped_categories, extracted_categories)
                        else:
                            extracted_categories = extract_categories_from(
                                scrapped_categories)
                            if extracted_categories:
                                categories = find_actual_parent(
                                    scrapped_categories, extracted_categories)

                    item["categories"] = categories
                    item["price"] = price
                    item["sizes"] = sizes
                    fabrics = []

                    for elem in f_details:
                        if "Lining" in elem or "Lace" in elem or "Yoke" in elem or "Strip" in elem or "Braid" in elem or "Embroidery" in elem:
                            break
                        if "%" in elem and elem.replace("Main Fabric : ", "").strip() != "":
                            fabrics.append(elem.replace("Main Fabric : ", "").replace(
                                "Main material : ", "").strip())

                    if len(fabrics) == 0:
                        fabrics = [elem.strip()
                                   for elem in f_details if "%" in elem]

                    item["fabric"] = ", ".join(fabrics)
                    item["fit"] = parse_keywords(
                        FIT_KEYWORDS, name, details, string=True)
                    item["colors"] = colors

                    details = [" ".join(detail.split(
                    )) for detail in details if "Behind the label" not in detail and "%" not in detail]

                    item["details"] = details
                    item["images"] = images
                    item["number_of_reviews"] = ""
                    item["review_description"] = []
                    item["top_best_seller"] = ""
                    item["style"] = parse_keywords(
                        STYLE_KEYWORDS, name, details)
                    item["length"] = parse_keywords(
                        LENGTH_KEYWORDS, name, details, string=True)
                    item["neck_line"] = parse_keywords(
                        NECK_LINE_KEYWORDS, name, details, string=True
                    )
                    item["occasions"] = parse_keywords(
                        OCCASIONS_KEYWORDS, name, details)
                    # item["aesthetics"] = parse_keywords(
                    #     AESTHETIC_KEYWORDS, name, details, string=True
                    # )
                    item["gender"] = gender
                    category_value = ""
                    meta = {}
                    if categories:
                        for key in my_dict:
                            if categories[0] in my_dict[key]:
                                category_value = key
                                break
                    meta["category"] = category_value
                    item["meta"] = meta
                    item["website_name"] = WEBSITE_NAME

                    break
                except Exception as e:
                    item = None
                    print("**************", url, "\n", str(e))
            if categories:
                if sizes:
                    yield item


# This function maps category we have extracted from name or url to taxonomy,
# and then it returns the list of extracted keywords.
def map_to_parents(cats):
    # where cats -> categories
    # cat -> category
    finals = []
    for cat in cats:
        for key in CATEGORY_TO_TYPE:
            if re.search(cat, ' '.join(CATEGORY_TO_TYPE[key]), re.IGNORECASE):
                finals.append(key)
    if not finals:
        for cat in cats:
            for key in CATEGORY_TO_STYLE:
                if re.search(cat, ' '.join(CATEGORY_TO_STYLE[key]), re.IGNORECASE):
                    finals.append(key)
    return list(set(finals))


# This function find real parent category from the list of extracted categories we provided
# Arguments: -> here first arg is scrapped categories and second is one which is list of extracted keywords
# we basically loop over scrapped categories and check if any category from scrapped one lies in extracted ones
def find_actual_parent(scrapped_cats, categories):
    finals = []
    final_categories = map_to_parents(categories)
    if len(final_categories) > 1:
        for fc in final_categories:
            if re.search(fc, ' '.join(scrapped_cats), re.IGNORECASE):
                finals.append(fc)

        if finals:
            return finals
        else:
            return []
    else:
        if final_categories:
            return final_categories
        else:
            return []


# This function extracts category keywords from product attribute passed as an argument to it
def extract_categories_from(keyword):
    cats = []  # categories
    if type(keyword) == list:
        keyword = ' '.join(keyword)

    for cat in CATEGORY_KEYWORDS:
        if re.search(cat, keyword, re.IGNORECASE):
            cats.append(cat)

    return cats


def parse_keywords(KEYWORDS, title, details, string=False):
    keywords_list = []
    title = title.lower()
    for keyword in KEYWORDS:
        keylower = keyword.lower()
        if keylower in title:
            keywords_list.append(keyword)
        else:
            for detail in details:
                if keylower in detail:
                    keywords_list.append(keyword)
                    break
    if not string:
        return keywords_list
    else:
        return ",  ".join(keywords_list)

import scrapy
from scrapy import Selector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import re
from webdriver_manager.chrome import ChromeDriverManager
from ..items import FashionnovaScrapperItem
from itertools import chain
import os
import time
# Constants
SCROLL_PAUSE_TIME = 5  # Scroll pause time for scrapping pages having infinite scroll
DISALLOWED_CATEGORIES = ["shoes", "accessories", "sandals", "nova-sport", "jogger", "joggers"
                         "all", "new", "back-in-stock", "#", "sale", "nova-essentials"]

ALLOWED_CATEGORIES = ["bikni", "blouses", "camis", "tanks", "sweatshirts", "sweatpants", "hoodies", "skirts",
                      "leggings", "jackets", "swimwear", "lounge", "jeans", "Tee", "T-Shirt", "Jersey",
                      "Mini", "Midi", "Maxi", "Formal", "Summer", "Long Sleeve", "Satin", "Blazer", "Maternity",
                      "Plus", "Petite", "Snatched", "Skinny", "Baggy", "Flare", "Wide", "Cargo"]

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


CATEGORY_KEYWORDS = ["Mini Dress", "Midi Dress", "Maxi Dress", "Petite", "Maternity", "Linen", "Tops",
                     "Shorts", "Jeans", "Jumpsuits", "Rompers", "Swimwear", "Blouses", "Blazer", "Pants", "Jackets",
                     "Coats", "Hoodies", "Lingere", "Loungewear"]


class FashionnovaSpider(scrapy.Spider):
    name = 'fashionnova'
    allowed_domains = ['www.fashionnova.com']

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
    # This method starts initial requests for scrapy

    def start_requests(self):
        url = "https://www.fashionnova.com/collections/women"
        yield scrapy.Request(url=url, callback=self.parse_total_products)

    # This function parses categories for site

    def parse_total_products(self, response):
        self.driver.get(response.request.url)
        self.driver.implicitly_wait(20)
        custom_response = Selector(text=self.driver.page_source)
        total_products = custom_response.css(
            "span[data-paginate-total]::text").get()
        if (total_products):
            total_products = int(total_products.replace(",", ""))
            totalPages = total_products // 48 + 1
            for page in range(1, totalPages + 1):
                url = f"{response.request.url}?page={page}"
                yield scrapy.Request(url=url, callback=self.get_all_products, dont_filter=True)

    # This function, parse href of all products on current page

    def get_all_products(self, response):
        self.driver.get(response.request.url)
        self.scroll_to_bottom()
        custom_response = Selector(text=self.driver.page_source)
        products = custom_response.css(
            "div.product-tile__product-title a::attr('href')").getall()
        for product_url in products:
            yield scrapy.Request(url=response.urljoin(product_url), callback=self.parse_product)

    # This function parses product details
    def parse_product(self, response):
        try:
            self.driver.get(response.request.url)
            time.sleep(3)
            custom_response = Selector(text=self.driver.page_source)
            url = response.request.url
            external_id = custom_response.xpath(
                "//form[@class='product-info__form product-form'] /@id").get()
            if external_id:
                external_id = external_id.split("_")[-1]

            name = response.css(".product-info__title::text").get()
            price = custom_response.xpath(
                "//div[@class='product-info__price-line'] /div /div[1] /text()").get()
            if not price:
                price = custom_response.xpath(
                    "//div[@class='product-info__price-line'] /div /div[2] /text()").get()

            sizes = custom_response.css(
                "div.product-info__size-buttons label span.product-info__size-button-label::text").getall()
            sizes = self.clean_sizes(sizes)

            details = response.css(
                "div.product-info__details-body li ::text").getall()
            details = self.clean_details(details)
            fabric = self.find_fabric_from_details(details) if details else ""
            images = custom_response.xpath(
                "//div[@class='product-slideshow__mainSlide'] /div[contains(@class, 'product-slideshow')] //img /@src").getall()
            images = ["https:"+image for image in images]
            categories = response.xpath(
                "//nav[@class='breadcrumbs'] //text()").extract()
            categories = [item.strip() for item in categories if item.strip()]
            categories = categories[1: -1]
            for keyword in CATEGORY_KEYWORDS:
                if re.search(keyword, name, re.IGNORECASE) or re.search(keyword, response.request.url, re.IGNORECASE):
                    categories.append(keyword)

            categories = self.clean_categories(categories)
            colors = custom_response.css(
                "p.product-info__color-name::text").get()
            if colors:
                colors = colors.split("/")
                colors = [color.strip() for color in colors]
            else:
                colors = []

            fit = self.find_from_target_string_single(details, FIT_KEYWORDS)
            neck_line = self.find_from_target_string_single(
                details, NECK_LINE_KEYWORDS)
            length = self.find_from_target_string_multiple(
                details, name, categories, LENGTH_KEYWORDS)
            gender = "women"
            # Extracting Number of reviews
            review_description = custom_response.css(
                "span.product-review-content::text").getall()
            if not review_description:
                review_description = ""

            number_of_reviews = str(len(review_description))
            top_best_seller = ""
            occasions = self.find_from_target_multiple_list(
                details, name, categories, OCCASIONS_KEYWORDS)
            style = self.find_from_target_multiple_list(
                details, name, categories, STYLE_KEYWORDS)
            meta = {}
            website_name = "fashionnova"
            # aesthetics = self.find_from_target_string_multiple(details, name, categories, AESTHETIC_KEYWORDS)

            item = FashionnovaScrapperItem()
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
            if categories and not self.in_disallowed_categories(name, url, categories):
                yield item
        except Exception as e:
            print(e)

    def in_disallowed_categories(self, name, url, categories):
        for keyword in DISALLOWED_CATEGORIES:
            if (re.search(keyword, f"{name} {url} {' '.join(categories)}", re.IGNORECASE)):
                return True

        return False
    # This function scrolls product detail page to the bottom

    def scroll_to_bottom(self):
        last_height = self.driver.execute_script(
            "return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(8)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script(
                "return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    # This method finds, if provided category name lies in category
    # keywords, it will return that else ""

    def clean_and_map_category(self, category):
        if "matching-sets" in category:
            return ["matching sets"]

        categories = category.split("/")[-1].split("-")
        return [category.strip() for category in categories if category != "and"]

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

    # This helper method clean details we have scrapped
    def clean_details(self, details):
        # Removing newline and empty string character from details
        details = [detail for detail in details if detail !=
                   "" and detail != "\n"]
        # Striping each elements in details list
        details = [detail.strip().replace("\u00a0", "") for detail in details]
        return details

    # This helper finds fabric from details and returns it
    def find_fabric_from_details(self, details):
        product_details = ' '.join(details)
        fabrics_founded = re.findall(r"""(\d+ ?%\s?)(.*)(
            velvet\b|silk\b|satin\b|cotton\b|lace\b|
            sheer\b|organza\b|chiffon\b|spandex\b|polyester\b|
            poly\b|linen\b|nylon\b|viscose\b|Georgette\b|Ponte\b|
            smock\b|smocked\b|shirred\b|Rayon\b|Bamboo\b|Knit\b|Crepe\b|
            Leather\b|polyamide\b|Acrylic\b|Elastane\bTencel\bCashmere\b)\)?""", product_details, flags=re.IGNORECASE | re.MULTILINE)

        return re.sub("\(|\)", "", ' '.join([''.join(tups) for tups in fabrics_founded]))

    # This function clean sizes

    def clean_sizes(self, sizes):
        sizes = [size.strip() for size in sizes]
        sizes = [size for size in sizes if len(size) != 0]
        return sizes

    def remove_duplicates_using_regex(self, keywords_list):
        finals = []
        for keyword in keywords_list:
            if not re.search(keyword, ' '.join(finals), re.IGNORECASE):
                finals.append(keyword)

        return finals

    def clean_categories(self, categories):
        categories = [cat for cat in categories if not re.search("women", cat, re.IGNORECASE) and
                      not re.search("men", cat, re.IGNORECASE)]
        categories = [cat.split(" ") for cat in categories]
        categories = list(chain.from_iterable(categories))
        categories = [cat for cat in categories if cat != "" and not re.search("Men", cat, re.IGNORECASE) and
                      not re.search("Women", cat, re.IGNORECASE)]
        categories = [cat for cat in categories if cat != ""]
        return self.remove_duplicates_using_regex(categories)

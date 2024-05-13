from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
import pickle
import random
import func_timeout

from bs4 import BeautifulSoup
from constants import TableHeaders
from utils import (
    get_absolute_url, 
    generate_time_gap, 
    match_address, 
    match_pets,
    match_bed,
    match_bath,
    match_price,
    match_sqft
)

import re
import time

#################################### High Level Comments ###################################
# Scraper class has methods for clicking buttons, scrolling the page, extracting information and handling errors
# These methods are coordinated via the extract_raw_data function in functions.py - entry point
# Only listing urls with more than 2 floorplans are extracted
# Assumes we do not want to prioritize listings by owners (not AM firms)
# Listings with >= 2 floorplans are definitely by AM firms - more accurate representation of competitor strategy
# Targeting all single unit listings also greatly increases scraping time without much benefit
# Wanted to minimize the number of HTTPS requests to avoid detection / blocking by website.
# Ensure the scraper operates stealthily before increasing the request frequency.
# TODO: Improve scraper speed and robustness to reliably handle single unit listings

class BaseScraper():
    """
    Abstract base class for building web scrapers.

    Attributes:
        base_url (str): Base URL of the site.
        urls (List[str]): List of URLs to scrape from.
        listings (List[dict]): All rental listings scraped.
    """
    def __init__(self, base_url=""):
        self.base_url = base_url
        self.urls = []
        self.listings = []
      
class PadmapperScraper(BaseScraper):
    """
    Web scraper specifically designed for the Padmapper website.

    Inherits from BaseScraper and adds methods tailored for scraping Padmapper.
    """
    def __init__(self, base_url=""):
        super().__init__(base_url)
        self.MAX_RETRIES = 3
        self.PAGE_LOAD_TIMEOUT = 15
        self.SCROLL_WAIT_TIME = 1
        self.UNIT_COUNT_THRESHOLD = 2
    
    def fetch_rental_listing_urls(self, web_driver: WebDriver, landing_page_url: str):
        """
        Retrieves and stores all the listing URLs from the landing page.

        Args:
            web_driver (WebDriver): The Selenium WebDriver to use for scraping.
            landing_page_url (str): The URL of the landing page to scrape.
        """
        print(f'********** Accessing {landing_page_url} **********')
        try:
            if self._try_load_page(web_driver, landing_page_url):
                self._click_tile_view_button(web_driver)
                try:
                    func_timeout.func_timeout(900, self._scroll_to_end_of_page, args=(web_driver,))
                except func_timeout.FunctionTimedOut:
                    print(f"Timeout reached when scrolling to bottom of {landing_page_url}")
                self.urls.extend(self._extract_urls(web_driver))
        except NoSuchElementException:
            print(f"Encountered error while scrolling {landing_page_url}")

    def _try_load_page(self, web_driver: WebDriver, url: str) -> bool:
        """
        Attempts to completely load the page and avoid perpetually loading state.

        Args:
            web_driver (WebDriver): The Selenium WebDriver to use for scraping.
            url (str): The URL of the page to load.

        Returns:
            bool: True if the page loads successfully, False otherwise.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                web_driver.get(url)
                WebDriverWait(web_driver, self.PAGE_LOAD_TIMEOUT).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'body'))
                )
                if web_driver.execute_script('return document.readyState') == 'complete':
                    return True
                else:
                    print(f"ERROR: Page Load Timeout on {url}")
            except TimeoutException:
                print(f"ERROR: Page Load Attempt {attempt + 1} failed for URL: {url}")
                web_driver.refresh()  
        return False
    
    def _click_tile_view_button(self, web_driver: WebDriver):
        """
        Clicks tile view button to switch to tile view from default block view.

        Args:
            web_driver (WebDriver): The Selenium WebDriver to use for scraping.
        """
        try:
            # Locate the button by class and aria-label attributes
            button = web_driver.find_element(by=By.CSS_SELECTOR, value="button[aria-label*='Tile'][class*='list_gridOptionIconContainer']")
            web_driver.execute_script("arguments[0].click();", button)
            time.sleep(self.SCROLL_WAIT_TIME)
        except NoSuchElementException:
            print("Tile View button not found. Unable to continue")
            raise

    def _scroll_to_end_of_page(self, web_driver: WebDriver):
        """
        Scrolls to the end of the page until no more content loads or a timeout is reached.

        Args:
            web_driver (WebDriver): The Selenium WebDriver to use for scraping.
        """
        last_height = web_driver.execute_script("return document.body.scrollHeight")

        while True:
            web_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1, 2)) 
            try:
                WebDriverWait(web_driver, 5).until(
                    lambda driver: driver.execute_script("return document.body.scrollHeight") > last_height
                )
                last_height = web_driver.execute_script("return document.body.scrollHeight")
            except TimeoutException:
                print("Reached the end of the page or no new content loaded.")
                break

    def _extract_urls(self, web_driver: WebDriver) -> list:
        """
        Extracts rental listing URLs from the home page.

        Args:
            web_driver (WebDriver): The Selenium WebDriver to use for scraping.

        Returns:
            List[str]: List of extracted URLs.
        """
        page_html_content = web_driver.page_source
        soup = BeautifulSoup(page_html_content, 'html.parser')

        extracted_urls = []
        # Get all rental listing URLs visible on the page
        link_elements = soup.find_all('a', class_=lambda cls: cls and cls.startswith('ListItemTile_address'))
        for link in link_elements:
            # Find the number of floorplans for the listing by getting the relevant sibling div
            for sibling in link.find_previous_siblings('div'):
                if any("ListItemTile_bedBath" in cls for cls in sibling.get('class', [])) and 'floorplan' in sibling.get_text().lower():
                    unit_count = int(sibling.get_text().split()[0])
                    if unit_count >= self.UNIT_COUNT_THRESHOLD:
                        # Extract the URL if number of floorplans is above threshold
                        print(f"Extracted {sibling.get_text()} for {get_absolute_url(self.base_url, link.get('href'))}")
                        extracted_urls.append(get_absolute_url(self.base_url, link.get('href')))
                        break  # Move to the next link element after finding the correct div
        return extracted_urls

    def _process_floorplan_panels(self, web_driver: WebDriver) -> bool:
        """
        Processes floorplan panels on the page if present.

        Args:
            web_driver (WebDriver): The Selenium WebDriver to use for scraping.

        Returns:
            bool: True if it's a single unit listing, False if multiple units are present.
        """
        try:
            dropdown_divs = WebDriverWait(web_driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class*='Floorplan_floorplanPanel']"))
            )
            for div in dropdown_divs:
                web_driver.execute_script("arguments[0].scrollIntoView();", div)
                web_driver.execute_script("arguments[0].click();", div)
                generate_time_gap(2, 3)
            return False
        except TimeoutException:
            return True  # If floorplan panels are not found, assume it's a single unit

    def get_rental_listing_data(self, web_driver: WebDriver, url: str) -> list:
        """
        Iterates over all collected URLs and scrapes data from each link's page.

        Args:
            web_driver (WebDriver): The Selenium WebDriver to use for scraping.
            url (str): URL of the listing page to scrape.

        Returns:
            list: List of rental listing data dictionaries.
        """
        try:
            if not self._try_load_page(web_driver, url):
                return []  # Skip processing this URL and continue with others
            
            # Wait for a summary table before proceeding
            WebDriverWait(web_driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='SummaryTable_']"))
            )
            
            is_single_unit = self._process_floorplan_panels(web_driver)
            link_html_content = web_driver.page_source
            print(f"Processing listing: {url}")
            return self._get_rental_units_data_by_listing(link_html_content, is_single_unit, url)
        
        except Exception as e:
            print(f"Error encountered on page {url}: {e}")
            raise
    
    def _get_rental_units_data_by_listing(self, link_html_content: str, is_single_unit: bool, url: str) -> list:
        """
        Extracts relevant data for each rental unit on listing (can be single unit).

        Args:
            link_html_content (str): The HTML content of the page to be scraped.
            is_single_unit (bool): Whether the listing is a single unit or has multiple units.
            url (str): URL of the listing page.

        Returns:
            list: A list of dictionaries, each containing data for a rental unit.
        """
        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(link_html_content, 'html.parser')
        
        building_title_text, neighborhood_title_text, price_text, bed_text, bath_text, sqft_text, address_text, pets_text, lat_text, lon_text, city_text = DataExtractor.extract_building_details(soup)

        unit_amenities_text, building_amenities_text = DataExtractor.extract_amenities(soup)

        all_units_data = DataExtractor.extract_rental_unit_details(soup)

        # For single page listings, all_units_data is already extracted from extract_building_details(), extract_rental_unit_details() will return empty
        all_units_data = all_units_data if not is_single_unit else [
            {
                TableHeaders.LISTING.value: bed_text,
                TableHeaders.BED.value: bed_text,
                TableHeaders.PRICE.value: price_text,
                TableHeaders.BATH.value: bath_text,
                TableHeaders.SQFT.value: sqft_text,
            }
        ]

        rental_listing_units = []

        # Concatenate each row of rental unit data with columns for building and rental unit amenities
        for unit_data in all_units_data:
            unit_data[TableHeaders.BUILDING.value] = building_title_text
            unit_data[TableHeaders.NEIGHBOURHOOD.value] = neighborhood_title_text
            unit_data[TableHeaders.PETS.value] = pets_text
            unit_data[TableHeaders.UNIT_AMENITIES.value] = unit_amenities_text
            unit_data[TableHeaders.BUILDING_AMENITIES.value] = building_amenities_text
            unit_data[TableHeaders.ADDRESS.value] = address_text
            unit_data[TableHeaders.CITY.value] = city_text
            unit_data[TableHeaders.LAT.value] = lat_text
            unit_data[TableHeaders.LON.value] = lon_text
            unit_data[TableHeaders.URL.value] = url
            rental_listing_units.append(unit_data)

        self.listings += rental_listing_units
        print(f"Extracted {len(rental_listing_units)} units in {city_text}")
        print(f"Total units: {len(self.listings)}")
        with open('listings.pkl', 'wb') as file:
            pickle.dump(self.listings, file)
        return rental_listing_units
        
class DataExtractor():
    @staticmethod
    def extract_building_details(soup: BeautifulSoup) -> tuple:
        """
        Extracts building details from the listing page.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object to extract data from.

        Returns:
            tuple: A tuple containing building details.
        """
        building_title = soup.find('h1', class_=lambda cls: cls and 'FullDetail_street_' in cls)
        building_title_text = re.split(r'[^\w ]+',  building_title.get_text())[0] if building_title else ""

        neighborhood_title_sep = soup.find('span', class_=lambda cls: cls and 'FullDetail_cityStateDivider_' in cls)
        neighborhood_title = neighborhood_title_sep.find_next_sibling('a', class_=lambda cls: cls and 'FullDetail_cityStateLink_' in cls)
        neighborhood_title_text = re.split(r'[^\w ]+',  neighborhood_title.get_text())[0] if neighborhood_title else ""

        details = soup.find('div', class_=lambda cls: cls and 'SummaryTable_summaryTable_' in cls)

        [price_text, bed_text, bath_text, sqft_text, address_text, pets_text] = DataExtractor.extract_summary_table(details)

        # Find the latitude meta tag
        latitude_tag = soup.find('meta', {'name': 'place:location:latitude'})
        lat_text = latitude_tag['content'] if latitude_tag else ""

        # Find the longitude meta tag
        longitude_tag = soup.find('meta', {'name': 'place:location:longitude'})
        lon_text = longitude_tag['content'] if longitude_tag else ""

        # Find the city meta tag
        city_tag = soup.find('meta', {'name': 'place:locality'})
        city_text = city_tag['content'] if city_tag else ""

        return (building_title_text, neighborhood_title_text, price_text, bed_text, bath_text, sqft_text, address_text, pets_text, lat_text, lon_text, city_text)

    @staticmethod
    def extract_summary_table(soup: BeautifulSoup) -> list:
        """
        Extracts summary table details from the listing page.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing the summary table.

        Returns:
            list: A list of extracted details.
        """
        extracted_text = []
        for matching_function in [match_price, match_bed, match_bath, match_sqft, match_address, match_pets]:
            detail_header = soup.find(matching_function)
            parent_detail_li = detail_header.find_parent('li') if detail_header else None
            detail_div = parent_detail_li.find('div') if parent_detail_li else None
            detail_text = detail_div.get_text().strip() if detail_div else ""
            extracted_text.append(detail_text)
        return extracted_text

    @staticmethod
    def extract_amenities(soup: BeautifulSoup) -> tuple:
        """
        Extracts text of unit and building amenities.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object to extract data from.

        Returns:
            tuple: A tuple containing text of unit amenities and building amenities.
        """
        amenities = soup.find_all('div', class_=lambda value: value and 'Amenities_header_' in value)
        unit_amenities, building_amenities = [], []
        try:
            unit_amenities_header = amenities[0] if len(amenities) == 2 and "apartment" in amenities[0].get_text().lower() else ""
            building_amenities_header = amenities[1] if len(amenities) == 2 and "building" in amenities[1].get_text().lower() else ""
            unit_amenities_container = unit_amenities_header.find_parent('div') if unit_amenities_header else ""
            building_amenities_container = building_amenities_header.find_parent('div') if building_amenities_header else ""
            unit_amenities = unit_amenities_container.find_all('div', class_=lambda cls: cls and 'Amenities_text_' in cls) if unit_amenities_container else []
            building_amenities = building_amenities_container.find_all('div', class_=lambda cls: cls and 'Amenities_text_' in cls) if building_amenities_container else []
        except Exception as e:
            print("Error - Getting amenities: ", e)
            
        unit_amenities_text = ", ".join([amenity.get_text() for amenity in unit_amenities])  
        building_amenities_text = ", ".join([amenity.get_text() for amenity in building_amenities])  

        return (unit_amenities_text, building_amenities_text)

    @staticmethod
    def extract_rental_unit_details(soup: BeautifulSoup) -> list:
        """
        Extracts rental unit details from the listing page.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object to extract data from.

        Returns:
            list: A list of dictionaries, each containing data for a rental unit.
        """
        all_units_data = []

        # Find all divs where class contains 'Floorplan_floorplan'
        floorplans = soup.find_all('div', class_=lambda cls: cls and 'Floorplan_floorplansContainer_' in cls)
        for floorplan in floorplans:
            current_floorplan = floorplan.find('div', class_=lambda cls: cls and 'Floorplan_title_' in cls)
            floorplan_title_text = current_floorplan.get_text().strip() if current_floorplan else ""
            
            unit_containers = floorplan.find_all('div', class_=lambda cls: cls and 'Floorplan_floorplanDetailContainer_' in cls)
            for unit_container in unit_containers:
                unit_title = unit_container.find('div', class_=lambda cls: cls and 'Floorplan_floorplanTitle' in cls)
                unit_price = unit_container.find('div', class_=lambda cls: cls and 'Floorplan_floorplanPrice' in cls)
                unit_sqft = unit_container.find('div', class_=lambda cls: cls and 'Floorplan_sqft' in cls).find('span')
                unit_bath = unit_container.find('div', class_=lambda cls: cls and 'Floorplan_bath' in cls).find('span')
                
                unit_title_text = unit_title.get_text().strip() if unit_title else ""
                unit_price_text = unit_price.get_text().strip() if unit_price else ""
                
                unit_sqft_text = unit_sqft.get_text().strip() if unit_sqft else ""
                unit_sqft_text = unit_sqft_text if len(re.sub(r'[^\w]', '', unit_sqft_text)) >= 1 else ""
                
                unit_bath_text = unit_bath.get_text().strip() if unit_bath else ""
                unit_bath_text = unit_bath_text if len(unit_bath_text) >= 3 else ""
                
                unit_data = {
                    TableHeaders.LISTING.value: unit_title_text,
                    TableHeaders.BED.value: floorplan_title_text,
                    TableHeaders.BATH.value: unit_bath_text,
                    TableHeaders.SQFT.value: unit_sqft_text,
                    TableHeaders.PRICE.value: unit_price_text,
                }

                all_units_data.append(unit_data)
        
        return all_units_data
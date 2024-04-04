import os

import func_timeout

from constants import (
    table_columns, TableHeaders, PADMAPPER_BASE_URL
)

from config import (
    create_chrome_driver
)

from multiprocessing import Process, Queue

from scraper import PadmapperScraper

from selenium.webdriver.chrome.webdriver import WebDriver

import pandas as pd

from datetime import datetime

def extract_raw_data(filepath: str, listing_urls: list[str]) -> pd.DataFrame:
    extracted_listing_data = []

    for listing_url in listing_urls:
        # Initialize WebDriver for retrieving rental listings from landing page
        fetch_rental_listings_driver: WebDriver = create_chrome_driver(debugging_port=9222) 
        padmapper_scraper = PadmapperScraper(PADMAPPER_BASE_URL, [listing_url])
        # padmapper_scraper.fetch_rental_listing_urls(fetch_rental_listings_driver)

        # Close the fetch_rental_listing_driver
        fetch_rental_listings_driver.quit()

        # Initialize WebDriver for extracting data from every rental listing
        get_rental_data_driver: WebDriver = create_chrome_driver(debugging_port=9223)

        # Log all extracted listings to a txt file for data permanence
        with open('listings.txt', 'a') as file:
            file.write('\n'.join(padmapper_scraper.urls))
        
        current_100_units = []

        # Scrape page content of collected URLs to get rental listing data 
        for url in padmapper_scraper.urls:
            try:
                # on every 100 listings read, write them to the excel sheet (in case of crash)
                if len(current_100_units) >= 100:
                    extracted_listing_data += current_100_units
                    extracted_listing_data_df = pd.DataFrame(extracted_listing_data, columns=table_columns)
                    extracted_listing_data_df.to_excel(filepath, index=False)
                    current_100_units.clear()
                
                try:
                    rental_listing_data = func_timeout.func_timeout(30, padmapper_scraper.get_rental_listing_data, args=(get_rental_data_driver, url))
                except func_timeout.FunctionTimedOut:
                    get_rental_data_driver.quit()
                    get_rental_data_driver = create_chrome_driver(debugging_port=9223)
                    print(f"Function timed out on url {url}")
                    
                if rental_listing_data:
                    current_100_units += rental_listing_data
                    
            except:
                continue

        # Append remaining padmapper listings to all_units
        extracted_listing_data += current_100_units

        extracted_listing_data_df = pd.DataFrame(extracted_listing_data, columns=table_columns)

        extracted_listing_data_df.to_excel(filepath, index=False)

        # Close the get_rental_data_driver
        get_rental_data_driver.quit()

    extracted_listing_data_df[TableHeaders.DATE.value] = pd.to_datetime(extracted_listing_data_df[TableHeaders.DATE.value], errors='coerce')
    extracted_listing_data_df[TableHeaders.DATE.value] = extracted_listing_data_df[TableHeaders.DATE.value].fillna(datetime.now())    
    
    extracted_listing_data_df.to_excel(filepath, index=False)

    return extracted_listing_data_df
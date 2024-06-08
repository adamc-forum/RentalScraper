import os
import re
import func_timeout
import pandas as pd

from constants import (
    TableHeaders, UnitAmenitiesDict, BuildingAmenitiesDict
)

from constants import (
    table_columns, TableHeaders, PADMAPPER_BASE_URL
)

from config import create_chrome_driver
from scraper import PadmapperScraper
from selenium.webdriver.chrome.webdriver import WebDriver
from datetime import datetime

#################################### High Level Comments ###################################
# Used separate drivers for fetching and scraping listing urls
# Preferred explicitly creating a new driver instance in case previous instance disconnected
# Fetching urls driver visits regional landing pages e.g. https://www.padmapper.com/apartments/toronto-on
# Scraping urls driver visits each url extracted by fetching urls driver

def extract_raw_data(filepath: str, landing_page_urls: list[str]) -> pd.DataFrame:
    """
    Extracts raw rental listing data from provided URLs and saves it to an Excel file.

    Args:
        filepath (str): The path to save the extracted data Excel file.
        landing_page_urls (list[str]): A list of regional landing page URLs to scrape for rental listings.

    Returns:
        pd.DataFrame: A DataFrame containing the extracted rental listing data.
    """
    extracted_listing_data = []

    for landing_page_url in landing_page_urls:
        
        # Initialize web driver for retrieving rental listings from regional landing page
        fetch_rental_listings_driver: WebDriver = create_chrome_driver(debugging_port=9222) 
        padmapper_scraper = PadmapperScraper(PADMAPPER_BASE_URL)
        padmapper_scraper.fetch_rental_listing_urls(web_driver=fetch_rental_listings_driver, landing_page_url=landing_page_url)

        fetch_rental_listings_driver.quit()

        # Initialize web driver for extracting data from every extracted rental listing
        get_rental_data_driver: WebDriver = create_chrome_driver(debugging_port=9223)

        current_100_units = []
        all_listings_data = []
        
        print(f"***** Extracted {len(padmapper_scraper.urls)} listings for {landing_page_url.split('/')[-1]} *****")
        print(f"{'\n'.join(padmapper_scraper.urls)}")

        # Scrape page content of scraped listing URLs to get rental listing data 
        for url in padmapper_scraper.urls:
            try:
                try_count = 0

                # Max retries for attempting to scrape a url
                max_retries = 3  

                while try_count < max_retries:
                    try:
                        # Attempt to scrape url with a 30 second time limit
                        # If function times out or no data was extracted, retry upto 3 times
                        # Else, data was retrieved successful, break and exit the loop

                        listing_data = func_timeout.func_timeout(30, padmapper_scraper.get_rental_listing_data, args=(get_rental_data_driver, url))
                        if len(listing_data) == 0:
                            print(f"ERROR: Extracted 0 units on url {url}, retrying...")
                        else:
                            break
                    except func_timeout.FunctionTimedOut:
                        print(f"ERROR: Function timed out on url {url}, retrying...")
                    finally:
                        try_count += 1
                        get_rental_data_driver.quit()
                        get_rental_data_driver = create_chrome_driver(debugging_port=9223)
                        get_rental_data_driver.refresh()

                # Every 100 listings, write to the Excel sheet (in case web driver crashes)
                if len(current_100_units) >= 100:
                    all_listings_data += current_100_units
                    all_listings_data_df = pd.DataFrame(all_listings_data, columns=table_columns)
                    all_listings_data_df.to_excel(filepath, index=False)
                    current_100_units.clear()

                if listing_data:
                    current_100_units += listing_data

            except:
                print(f"Error occurred on url: {url}")
                continue

        # Append remaining padmapper listings to all listings
        all_listings_data += current_100_units

        all_listings_data_df = pd.DataFrame(all_listings_data, columns=table_columns)

        all_listings_data_df.to_excel(filepath, index=False)

        # Close the get_rental_data_driver
        get_rental_data_driver.quit()

    all_listings_data_df[TableHeaders.DATE.value] = pd.to_datetime(all_listings_data_df[TableHeaders.DATE.value], errors='coerce')
    all_listings_data_df[TableHeaders.DATE.value] = all_listings_data_df[TableHeaders.DATE.value].fillna(datetime.now())    
    
    all_listings_data_df.to_excel(filepath, index=False)

    return all_listings_data_df

################## Parsing and validation functions #################

def parse_bed_value(bed_value):
    """
    Parses the bed value from a listing and returns the number of bedrooms.

    Args:
        bed_value: The value representing the number of bedrooms.

    Returns:
        int or None: The number of bedrooms, or None if parsing fails.
    """
    if pd.isna(bed_value):
        return bed_value
    bed_value = bed_value.lower()
    if 'bedroom' in bed_value or ('studio' in bed_value and 'room' not in bed_value):
        try:
            return 0 if "studio" in bed_value else int(bed_value.split(' ')[0])
        except (ValueError, IndexError):
            return None
    return None


def parse_bath_value(bath_value):
    """
    Parses the bath value from a listing and returns the number of bathrooms.

    Args:
        bath_value: The value representing the number of bathrooms.

    Returns:
        float or None: The number of bathrooms, or None if parsing fails.
    """
    if pd.isna(bath_value):
        return bath_value
    try:
        if ',' in bath_value:
            full_bath, half_bath = bath_value.split(',')
            return int(full_bath.strip().split(' ')[0]) + 0.5 * int(half_bath.strip().split(' ')[0])
        return int(bath_value.strip().split(' ')[0])
    except (ValueError, IndexError):
        return None


def parse_sqft_value(sqft_value):
    """
    Parses the square footage value from a listing.

    Args:
        sqft_value: The value representing the square footage.

    Returns:
        int or None: The square footage, or None if parsing fails.
    """
    if pd.isna(sqft_value) or re.search(r'\d', sqft_value) is None:
        return None
    sqft_value = int(sqft_value.replace(',', '').split(' ')[0])
    return sqft_value


def parse_price_value(price_value):
    """
    Parses the price value from a listing and returns the minimum, maximum, and average prices.

    Args:
        price_value: The value representing the price.

    Returns:
        tuple: A tuple containing the minimum, maximum, and average prices, or None if parsing fails.
    """
    if pd.isna(price_value):
        return None, None, None
    price_value = price_value.replace('$', '').replace(',', '')
    if '—' in price_value:
        min_price, max_price = price_value.split('—')
        try:
            min_price = int(min_price)
            max_price = int(max_price)
            avg_price = (min_price + max_price) / 2
            return min_price, max_price, avg_price
        except ValueError:
            return None, None, None
    try:
        price = int(price_value)
        return price, price, price  # Min, Max, and Avg are the same for a single price
    except ValueError:
        return None, None, None

def parse_building_amenities(amenities_value):
    """
    Parses the building amenities value from a listing.

    Args:
        amenities_value: The value representing the building amenities.

    Returns:
        list or None: A list of building amenities, or None if parsing fails.
    """
    if not pd.isna(amenities_value):
        return [amenity.strip() for amenity in amenities_value.split(',') if amenity.strip() in BuildingAmenitiesDict]
    return None


def parse_unit_amenities(amenities_value):
    """
    Parses the unit amenities value from a listing.

    Args:
        amenities_value: The value representing the unit amenities.

    Returns:
        list or None: A list of unit amenities, or None if parsing fails.
    """
    if not pd.isna(amenities_value):
        return [amenity.strip() for amenity in amenities_value.split(',') if amenity.strip() in UnitAmenitiesDict]
    return None


def parse_pets_value(pets_value):
    """
    Parses the pets allowed value from a listing.

    Args:
        pets_value: The value representing whether pets are allowed.

    Returns:
        int: 1 if pets are allowed, 0 otherwise.
    """
    if pd.isna(pets_value):
        return 0
    pets_value = pets_value.lower()
    return 1 if any(pet in pets_value for pet in ['dog', 'cat', 'yes']) else 0

def get_raw_df(raw_filepath: str) -> pd.DataFrame:
    """
    Reads a raw Excel file and returns it as a DataFrame.

    Args:
        raw_filepath (str): The path to the raw data Excel file.

    Returns:
        pd.DataFrame: A DataFrame containing the raw data.
    """
    return pd.read_excel(raw_filepath)

def get_cleaned_data(df):
    """
    Cleans and processes the raw data DataFrame.

    Args:
        df (pd.DataFrame): The raw data DataFrame.

    Returns:
        pd.DataFrame: A cleaned and processed DataFrame.
    """
    df[TableHeaders.BED.value] = df[TableHeaders.BED.value].apply(parse_bed_value)
    df[TableHeaders.BATH.value] = df[TableHeaders.BATH.value].apply(parse_bath_value)
    df[TableHeaders.SQFT.value] = df[TableHeaders.SQFT.value].apply(parse_sqft_value)

    price_parsed = df[TableHeaders.PRICE.value].apply(parse_price_value)
    df[TableHeaders.PRICE.value] = price_parsed.apply(lambda x: x[2]) 
    df['Min Price'] = price_parsed.apply(lambda x: x[0])
    df['Max Price'] = price_parsed.apply(lambda x: x[1])

    df[TableHeaders.PETS.value] = df[TableHeaders.PETS.value].apply(parse_pets_value)
    df[TableHeaders.BUILDING_AMENITIES.value] = df[TableHeaders.BUILDING_AMENITIES.value].apply(parse_building_amenities)
    df[TableHeaders.UNIT_AMENITIES.value] = df[TableHeaders.UNIT_AMENITIES.value].apply(parse_unit_amenities)

    # Flatten out the building amenities into one-hot encoded columns
    df_exploded = df.explode(TableHeaders.BUILDING_AMENITIES.value)
    dummies = pd.get_dummies(df_exploded, columns=[TableHeaders.BUILDING_AMENITIES.value], prefix='', prefix_sep='', dtype=int)
    df = dummies.groupby(dummies.index).max()

    # Flatten out the unit amenities into one-hot encoded columns
    df_exploded = df.explode(TableHeaders.UNIT_AMENITIES.value)
    dummies = pd.get_dummies(df_exploded, columns=[TableHeaders.UNIT_AMENITIES.value], prefix='', prefix_sep='', dtype=int)
    df = dummies.groupby(dummies.index).max()

    df[TableHeaders.DATE.value] = pd.to_datetime(df[TableHeaders.DATE.value], errors='coerce').fillna(datetime.now())
    df[TableHeaders.DATE.value] = df[TableHeaders.DATE.value].dt.strftime("%b %Y")

    # Reorder columns to ensure price columns are together
    price_index = df.columns.get_loc(TableHeaders.PRICE.value)
    columns = list(df.columns)
    columns.insert(price_index, columns.pop(columns.index('Min Price')))
    columns.insert(price_index + 1, columns.pop(columns.index('Max Price')))
    df = df[columns]

    # Reorder columns to move URL to the end
    lat_column = df.pop(TableHeaders.LAT.value)
    lon_column = df.pop(TableHeaders.LON.value)
    url_column = df.pop(TableHeaders.URL.value)
    date_column = df.pop(TableHeaders.DATE.value)
    df[TableHeaders.DATE.value] = date_column
    df[TableHeaders.LAT.value] = lat_column
    df[TableHeaders.LON.value] = lon_column
    df[TableHeaders.URL.value] = url_column

    # List of columns to check for NaN values
    na_columns_to_drop = [TableHeaders.BUILDING.value, TableHeaders.CITY.value, TableHeaders.BED.value, TableHeaders.BATH.value, TableHeaders.SQFT.value, TableHeaders.PRICE.value] 

    # Remove nulls
    df.dropna(subset=na_columns_to_drop, inplace=True)

    return df

def get_cleaned_df(raw_filepath: str, cleaned_filepath: str) -> pd.DataFrame:
    """
    Processes raw data from a file and saves the cleaned data to a new file.

    Args:
        raw_filepath (str): The path to the raw data file.
        cleaned_filepath (str): The path to save the cleaned data file.

    Returns:
        pd.DataFrame: A DataFrame containing the cleaned data.
    """
    cleaned_df = get_cleaned_data(get_raw_df(raw_filepath))
    cleaned_df.to_excel(cleaned_filepath, index=False)
    return cleaned_df
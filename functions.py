import os
import re

import func_timeout

from constants import TableHeaders, UnitAmenitiesDict, BuildingAmenitiesDict

from constants import (
    table_columns, TableHeaders, PADMAPPER_BASE_URL
)

from config import (
    create_chrome_driver
)

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
        padmapper_scraper.fetch_rental_listing_urls(fetch_rental_listings_driver)

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
                try_count = 0
                max_retries = 3  # Set a limit for retries

                while try_count < max_retries:
                    try:
                        rental_listing_data = func_timeout.func_timeout(30, padmapper_scraper.get_rental_listing_data, args=(get_rental_data_driver, url))
                        if len(rental_listing_data) == 0:
                            print(f"Extracted 0 units on url {url}, retrying...")
                        else:
                            break  # Exit the loop if data is successfully retrieved
                    except func_timeout.FunctionTimedOut:
                        print(f"Function timed out on url {url}, retrying...")
                    finally:
                        try_count += 1
                        get_rental_data_driver.quit()
                        get_rental_data_driver = create_chrome_driver(debugging_port=9223)
                        get_rental_data_driver.refresh()

                # On every 100 listings read, write them to the Excel sheet (in case of crash)
                if len(current_100_units) >= 100:
                    extracted_listing_data += current_100_units
                    extracted_listing_data_df = pd.DataFrame(extracted_listing_data, columns=table_columns)
                    extracted_listing_data_df.to_excel(filepath, index=False)
                    current_100_units.clear()

                if rental_listing_data:
                    current_100_units += rental_listing_data

            except:
                print(f"Error occured on url: {url}")
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

################## Parsing and validation functions #################

def parse_bed_value(bed_value):
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
    if pd.isna(sqft_value) or re.search(r'\d', sqft_value) is None:
        return None
    sqft_value = int(sqft_value.replace(',', '').split(' ')[0])
    return sqft_value


def parse_price_value(price_value):
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
    if not pd.isna(amenities_value):
        return [amenity.strip() for amenity in amenities_value.split(',') if amenity.strip() in BuildingAmenitiesDict]
    return None


def parse_unit_amenities(amenities_value):
    if not pd.isna(amenities_value):
        return [amenity.strip() for amenity in amenities_value.split(',') if amenity.strip() in UnitAmenitiesDict]
    return None


def parse_pets_value(pets_value):
    if pd.isna(pets_value):
        return 0
    pets_value = pets_value.lower()
    return 1 if any(pet in pets_value for pet in ['dog', 'cat', 'yes']) else 0

def get_raw_df(raw_filepath: str) -> pd.DataFrame:
    return pd.read_excel(raw_filepath)

# Main function to process the data
def get_cleaned_data(df):
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
    cleaned_df = get_cleaned_data(get_raw_df(raw_filepath))
    cleaned_df.to_excel(cleaned_filepath, index=False)
    return cleaned_df

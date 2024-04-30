from functions import (
    extract_raw_data,
    get_cleaned_df
)

import os
from datetime import datetime

current_dir = os.path.dirname(os.path.realpath(__file__))

current_timestamp = datetime.now().strftime("%m-%Y")

cleaned_data_files = os.listdir(os.path.join('data', 'cleaned_data'))

raw_filepath = f"{current_dir}/data/raw_data/{current_timestamp}_raw_listings.xlsx"
cleaned_filepath = f"{current_dir}/data/cleaned_data/{current_timestamp}_cleaned_listings.xlsx"

try:
    extract_raw_data(
        filepath=raw_filepath,
        listing_urls=[
            "https://www.padmapper.com/apartments/vancouver-bc",
            "https://www.padmapper.com/apartments/winnipeg-mb",
            "https://www.padmapper.com/apartments/toronto-on",
            "https://www.padmapper.com/apartments/ottawa-on",
            "https://www.padmapper.com/apartments/montreal-qc",
            "https://www.padmapper.com/apartments/edmonton-ab",
        ]
    )

    cleaned_data_df = get_cleaned_df(
        raw_filepath=raw_filepath, cleaned_filepath=cleaned_filepath
    )
except Exception as e:
    print("An error occurred while extracting data:", e)
    exit()
# RentalScraper

### Terminology

These terms that appear throughout the project are defined explicitly for the reader’s convenience to clarify precisely what they are referring to.

| Term              | Definition                                                                                          |
|-------------------|-----------------------------------------------------------------------------------------------------|
| Listing           | Contains all the units i.e. floor plans available to rent in a specific building.                   |
| Unit              | Refers to the specific apartment in a building available to rent, synonymous with floor plan.        |
| Amenities         | Refers to premiums included with a unit or a building.                                              |
| Unit amenities    | Balcony, In Unit Laundry, Air Conditioning, High Ceilings, Furnished, Hardwood Floor.               |
| Building amenities| Controlled Access, Fitness Center, Swimming Pool, Roof Deck, Storage, Residents Lounge, Outdoor Space.|

## Setup

This project runs on [Python](https://www.python.org/downloads/). Make sure you have a version of Python installed.

### Installing `chromedriver`

In order to run the web scrapers to extract rental listings data, you'll need to install `chromedriver`. Please visit the [chrome for testing website](https://googlechromelabs.github.io/chrome-for-testing/) to download chrome driver. Ensure the chrome driver version is the same as the version of google chrome on your machine.

Next, get the installation path:

```bash
where chromedriver
```

### Creating your environment

In the project directory, start by creating and activating a virtual environment:

```bash
python -m venv env # create virtual env named env
env/Scripts/activate # activate it
```

Then install all the project requirements:

```bash
pip install -r requirements.txt
```

Now create a `.env` file in the root directory by making a copy of [`.env.schema`](./.env.schema). Replace the `CHROMEDRIVER_PATH` variable in your `.env` file with your `chromedriver` installation path.

To determine values for other .env variables, you would either need to visit the azure portal or ask your manager. 

### Running the project

Running `main.py` in the root directory will commence the data acquisition process.

```bash
python -m main
```

For debugging purposes, you can run selenium in the non-headless mode by toggling this setting in `config.py`. This will enable you to see the web scraper interacting with a chrome window. 
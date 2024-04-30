from enum import Enum

class TableHeaders(Enum):
    BUILDING = 'Building'
    NEIGHBOURHOOD = 'Neighbourhood'
    ADDRESS = 'Address'
    CITY = 'City'
    LISTING = 'Listing'
    BED = 'Bed'
    BATH = 'Bath'
    SQFT = 'SqFt'
    UNIT_AMENITIES = 'Unit Amenities'
    BUILDING_AMENITIES =  'Building Amenities'
    PETS = 'Pets'
    PRICE = 'Price'
    LAT = 'Latitude'
    LON = 'Longitude'
    DATE = 'Date'
    URL = 'Url'

class UnitAmenities(Enum):
    BALCONY = 'Balcony'
    IN_UNIT_LAUNDRY = 'In Unit Laundry'
    AIR_CONDITIONING = 'Air Conditioning' 
    HIGH_CEILINGS = 'High Ceilings'
    FURNISHED = 'Furnished'
    HARDWOOD_FLOOR = 'Hardwood Floor'

class BuildingAmenities(Enum):
    CONTROLLED_ACCESS = 'Controlled Access'
    FITNESS_CENTER = 'Fitness Center'
    SWIMMING_POOL = 'Swimming Pool'
    ROOF_DECK = 'Roof Deck'
    STORAGE = 'Storage'
    RESIDENTS_LOUNGE = 'Residents Lounge'
    OUTDOOR_SPACE = 'Outdoor Space'


UnitAmenitiesDict = {
    UnitAmenities.BALCONY.value: 0,
    UnitAmenities.IN_UNIT_LAUNDRY.value: 0,
    UnitAmenities.AIR_CONDITIONING.value: 0,
    UnitAmenities.HIGH_CEILINGS.value: 0,
    UnitAmenities.FURNISHED.value: 0,
    UnitAmenities.HARDWOOD_FLOOR.value: 0
}

BuildingAmenitiesDict = {
    BuildingAmenities.CONTROLLED_ACCESS.value: 0,
    BuildingAmenities.FITNESS_CENTER.value: 0,
    BuildingAmenities.SWIMMING_POOL.value: 0,
    BuildingAmenities.ROOF_DECK.value: 0,
    BuildingAmenities.STORAGE.value: 0,
    BuildingAmenities.RESIDENTS_LOUNGE.value: 0,
    BuildingAmenities.OUTDOOR_SPACE.value: 0
}

table_columns = [table_header.value for table_header in TableHeaders]

PADMAPPER_BASE_URL = "https://www.padmapper.com"

SHAREPOINT_ROOT_FOLDER = "Rental Web Scraper"
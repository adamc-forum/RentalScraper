# Import necessary libraries
from fake_useragent import UserAgent
import random
import time

def get_headers(base_url):
    # Create a UserAgent object to generate random user agent strings
    user_agent = UserAgent().random

    # Loop to ensure the user agent is for Windows Chrome
    while not ('windows' in user_agent.lower() and 'chrome' in user_agent.lower()):
        user_agent = UserAgent().random

    # Set the headers to mimic a browser request from Chrome on Windows
    headers = {
        'User-Agent': user_agent,  
        'DNT': '1', 
        'Accept-Language': 'en-US,en;q=0.5', 
        'Referer': f'{base_url}', 
        'Sec-Ch-Ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"', 
        'Sec-Ch-Ua-Mobile': '?0', 
        'Sec-Ch-Ua-Platform': '"Windows"', 
        'Sec-Fetch-Dest': 'document', 
        'Sec-Fetch-Mode': 'navigate', 
        'Sec-Fetch-Site': 'same-origin', 
        'Sec-Fetch-User': '?1', 
        'Upgrade-Insecure-Requests': '1' 
    }
    return headers

def generate_time_gap(min=2, max=4):
    # Generates a random time delay to simulate human browsing and avoid server overload or detection
    time.sleep(random.uniform(min, max))

def get_absolute_url(base_url, href):
    # Constructs an absolute URL from a base URL and a relative URL (href)
    return href if href.startswith('http') else f'{base_url}{href}'

def make_matcher(tag_name, text):
    # Creates a function to match HTML tags with specific text content
    def match_tag(element):
        # Checks if the given tag contains the specified text
        return (
            tag_name in element.name and 
            text.lower() in element.get_text().lower().strip()
        )
    return match_tag

# Using make_matcher to create specific tag matchers
match_address = make_matcher('h', 'address') 
match_pets = make_matcher('h', 'dogs')  
match_sqft = make_matcher('h', 'feet')  
match_price = make_matcher('h', 'price') 
match_bed = make_matcher('h', 'bed') 
match_bath = make_matcher('h', 'bath') 
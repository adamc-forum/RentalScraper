from fake_useragent import UserAgent
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
import logging
import os

# Creates a Chrome Web Driver instance with certain configurations
# This is use case agnostic - should be consistent across different scraper applications

def create_chrome_driver(*, debugging_port):
    load_dotenv()

     # Create a UserAgent object to generate random user agent strings
    user_agent = UserAgent().random

    # Loop to ensure the user agent is for Windows Chrome
    while not ('windows' in user_agent.lower() and 'chrome' in user_agent.lower()):
        user_agent = UserAgent().random

    chrome_driver_path = os.getenv('CHROMEDRIVER_PATH') 

    # Set up chrome driver options
    chrome_options = ChromeOptions()
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument(f"--remote-debugging-port={debugging_port}")
    chrome_options.add_argument('--window-size=1920x1080')
    # chrome_options.add_argument("--headless")  # Enable headless mode (does not open browser GUI)
    chrome_options.add_argument("--log-level=3") 

    chrome_service = ChromeService(executable_path=chrome_driver_path)

    web_driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    return web_driver
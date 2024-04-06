from fake_useragent import UserAgent

from dotenv import load_dotenv
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
import logging

def create_chrome_driver(*, debugging_port):
    # Load environment variables from .env file
    load_dotenv()

    # Generate a random user agent
    user_agent = UserAgent().random

    # Access the WebDriver path from the environment variable
    chrome_driver_path = os.getenv('CHROMEDRIVER_PATH') 

    # Set up Chrome options (optional, for additional configurations)
    chrome_options = ChromeOptions()
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument(f"--remote-debugging-port={debugging_port}")
    chrome_options.add_argument('--window-size=1920x1080')
    chrome_options.add_argument("--headless")  # Enable headless mode (does not open browser GUI)
    chrome_options.add_argument("--log-level=3") 


    # Suppress console logs
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    # First ChromeService instance
    chrome_service = ChromeService(executable_path=chrome_driver_path)

    web_driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    return web_driver

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from twilio.rest import Client
from dotenv import load_dotenv
import os
import time
import shutil

# Load environment variables from .env file
load_dotenv()

# Twilio setup from .env
account_sid = os.getenv("ACCOUNT_SID")
auth_token = os.getenv("AUTH_TOKEN")
twilio_phone_number = os.getenv("TWILIO_PHONE")
your_phone_number = os.getenv("YOUR_PHONE")

client = Client(account_sid, auth_token)

def send_sms(message):
    print(f"Simulated SMS: {message}")
    # To actually send SMS, uncomment below:
    # client.messages.create(
    #     body=message,
    #     from_=twilio_phone_number,
    #     to=your_phone_number
    # )

def get_chrome_driver_path():
    # Try common Homebrew location
    chrome_path = shutil.which("chromedriver")
    if chrome_path:
        return chrome_path
    raise FileNotFoundError("ChromeDriver not found. Install it using Homebrew: `brew install --cask chromedriver`")

def check_for_table_records():
    driver = None

    try:
        chrome_driver_path = get_chrome_driver_path()

        # Set up Chrome options
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument('--disable-gpu')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

        service = Service(chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=options)

        retry_count = 3
        for attempt in range(retry_count):
            try:
                print("Navigating to login page...")
                driver.get("REPLACE_ME_WITH_LOGIN_URL")

                WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, 'Username')))
                print("Login page loaded.")

                username = os.getenv("LOGIN_USERNAME") or "REPLACE_ME"
                password = os.getenv("LOGIN_PASSWORD") or "REPLACE_ME"

                driver.find_element(By.ID, 'Username').send_keys(username)
                driver.find_element(By.ID, 'Password').send_keys(password)

                time.sleep(2)

                print("Attempting to login...")
                login_button = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Login")]'))
                )
                login_button.click()

                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'body'))
                )
                print("Logged in successfully.")

                print("Navigating to the Job Shop page...")
                driver.get("REPLACE_ME_WITH_JOB_SHOP_URL")

                WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
                print("Table found on the page.")

                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')

                table = soup.find('table', class_='table-striped')

                if table:
                    rows = table.find_all('tr')
                    if len(rows) > 1:
                        send_sms(f"Records found! Number of rows: {len(rows) - 1}")
                    else:
                        send_sms("No new records found.")
                else:
                    send_sms("Table not found.")

                break  # Success, exit retry loop

            except (TimeoutException, NoSuchElementException) as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                driver.save_screenshot(f"screenshot_attempt_{attempt + 1}.png")
                if attempt == retry_count - 1:
                    send_sms(f"Login failed after {retry_count} attempts.")
                time.sleep(5)

    except Exception as e:
        print(f"Critical error: {str(e)}")
        send_sms(f"Script failed: {str(e)}")

    finally:
        if driver:
            driver.quit()

# Run it
check_for_table_records()

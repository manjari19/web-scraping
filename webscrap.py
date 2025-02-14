from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from twilio.rest import Client
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Twilio setup (Removed actual credentials)
account_sid = "REPLACE_ME"
auth_token = "REPLACE_ME"
twilio_phone_number = "REPLACE_ME"
your_phone_number = "REPLACE_ME"

client = Client(account_sid, auth_token)

def send_sms(message):
    print(f"Simulated SMS: {message}")  # Logs instead of sending real SMS

def check_for_table_records():
    # Chromedriver path (Removed actual path)
    chrome_driver_path = "REPLACE_ME"

    # Set up Chrome options
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")  
    options.add_argument('--disable-gpu')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    # Define service
    service = Service(chrome_driver_path)

    # Set up the driver
    driver = webdriver.Chrome(service=service, options=options)

    retry_count = 3
    for attempt in range(retry_count):
        try:
            # Navigate to the login page
            print("Navigating to login page...")
            driver.get("REPLACE_ME_WITH_LOGIN_URL")

            # Wait for the username and password fields to appear
            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, 'Username')))
            print("Login page loaded.")

            # Fill in the login form securely
            username = "REPLACE_ME"
            password = "REPLACE_ME"

            driver.find_element(By.ID, 'Username').send_keys(username)
            driver.find_element(By.ID, 'Password').send_keys(password)

            # Add a short pause to ensure fields are filled before attempting login
            time.sleep(2)

            # Click the login button
            try:
                print("Attempting to login...")
                login_button = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Login")]'))
                )
                login_button.click()
            except NoSuchElementException:
                print("Login button not found.")
                send_sms("Login button not found.")
                return

            # Wait for the login to complete
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            print("Logged in successfully.")

            # Now navigate to the correct link
            print("Navigating to the Job Shop page...")
            driver.get("REPLACE_ME_WITH_JOB_SHOP_URL")

            # Wait for the table to appear on the page
            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
            print("Table found on the page.")

            # Get page source
            page_source = driver.page_source

            # Parse the page using BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')

            # Find the table by class
            table = soup.find('table', class_='table-striped')

            if table:
                rows = table.find_all('tr')
                if len(rows) > 1:
                    send_sms(f"Records found! Number of rows: {len(rows) - 1}")
                else:
                    send_sms("No new records found.")
            else:
                send_sms("Table not found.")

            break  # Exit retry loop if successful

        except (TimeoutException, NoSuchElementException) as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            driver.save_screenshot(f"screenshot_attempt_{attempt + 1}.png")  # Save screenshot for debugging
            if attempt == retry_count - 1:
                send_sms(f"Login failed after {retry_count} attempts.")
                return
            time.sleep(5)  # Wait before retrying

        finally:
            driver.quit()

# Run the function
check_for_table_records()

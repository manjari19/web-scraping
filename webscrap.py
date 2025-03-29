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

# Get secrets from environment (GitHub Actions)
account_sid = os.getenv("ACCOUNT_SID")
auth_token = os.getenv("AUTH_TOKEN")
twilio_phone_number = os.getenv("TWILIO_PHONE")
your_phone_number = os.getenv("YOUR_PHONE")
username = os.getenv("LOGIN_USERNAME")
password = os.getenv("LOGIN_PASSWORD")

# Debug check for secrets
print("Secrets loaded:")
print(f"ACCOUNT_SID set: {bool(account_sid)}")
print(f"AUTH_TOKEN set: {bool(auth_token)}")
print(f"TWILIO_PHONE set: {bool(twilio_phone_number)}")
print(f"YOUR_PHONE set: {bool(your_phone_number)}")
print(f"LOGIN_USERNAME set: {bool(username)}")
print(f"LOGIN_PASSWORD set: {bool(password)}")

client = Client(account_sid, auth_token)

def send_sms(message):
    short_msg = message if len(message) <= 1500 else message[:1500] + "..."
    print(f"Sending SMS: {short_msg}")
    client.messages.create(
        body=short_msg,
        from_=twilio_phone_number,
        to=your_phone_number
    )

def check_for_table_records():
    driver = None

    try:
        # Set up headless Chrome for GitHub Actions
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.binary_location = "/usr/bin/chromium-browser"
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)

        retry_count = 3
        for attempt in range(retry_count):
            try:
                print("Navigating to login page...")
                driver.get("https://bc38.atrieveerp.com/authenticationservice-Coquitlam/Account/Login")

                WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, 'Username')))
                print("Login page loaded.")

                driver.find_element(By.ID, 'Username').send_keys(username)
                driver.find_element(By.ID, 'Password').send_keys(password)
                time.sleep(2)

                print("Attempting to login...")
                login_button = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Login")]'))
                )
                login_button.click()

                WebDriverWait(driver, 60).until(
                    EC.url_contains("/Insights-coquitlam/Home/Index")
                )
                print("Login dashboard loaded. Now navigating to Job Shop...")

                driver.get("https://bc38.atrieveerp.com/coquitlam/servlet/Broker?env=ads&template=ads.JobShop1.xml")

                WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
                print("Table found on the page.")

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                table = soup.find('table', class_='table-striped')

                if table:
                    rows = table.find_all('tr')
                    if len(rows) > 1:
                        send_sms(f"Records found! Number of rows: {len(rows) - 1}")
                    else:
                        send_sms("No new records found.")
                else:
                    send_sms("Table not found.")

                break  # Success, exit loop

            except (TimeoutException, NoSuchElementException) as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                driver.save_screenshot(f"screenshot_attempt_{attempt + 1}.png")
                with open(f"page_source_attempt_{attempt + 1}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                if attempt == retry_count - 1:
                    send_sms("Login failed after 3 attempts.")
                time.sleep(5)

    except Exception as e:
        print(f"Critical error: {str(e)}")
        send_sms(f"Script failed: {str(e)}")

    finally:
        if driver:
            driver.quit()

# Run
check_for_table_records()

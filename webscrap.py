from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from twilio.rest import Client
from datetime import datetime
import os
import time

# ==== Timestamp Logging ====
print(f"\n=== Workflow run at: {datetime.utcnow().isoformat()} UTC ===\n")

# ==== Load Secrets ====
account_sid = os.getenv("ACCOUNT_SID")
auth_token = os.getenv("AUTH_TOKEN")
twilio_phone_number = os.getenv("TWILIO_PHONE")
your_phone_number = os.getenv("YOUR_PHONE")
username = os.getenv("LOGIN_USERNAME")
password = os.getenv("LOGIN_PASSWORD")

# ==== Confirm Secrets ====
print("Secrets loaded:")
print(f"ACCOUNT_SID set: {bool(account_sid)}")
print(f"AUTH_TOKEN set: {bool(auth_token)}")
print(f"TWILIO_PHONE set: {bool(twilio_phone_number)}")
print(f"YOUR_PHONE set: {bool(your_phone_number)}")
print(f"LOGIN_USERNAME set: {bool(username)}")
print(f"LOGIN_PASSWORD set: {bool(password)}")

client = Client(account_sid, auth_token)

# ==== Send SMS ====
def send_sms(message):
    short_msg = message if len(message) <= 1500 else message[:1500] + "..."
    print(f"\nSending SMS: {short_msg}")
    client.messages.create(
        body=short_msg,
        from_=twilio_phone_number,
        to=your_phone_number
    )

# ==== Main Check Logic ====
def check_for_table_records():
    driver = None

    try:
        # Headless Chrome for CI
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.binary_location = "/usr/bin/chromium-browser"
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        service = Service("/usr/lib/chromium-browser/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)

        retry_count = 3
        for attempt in range(retry_count):
            try:
                print(f"\n--- Attempt {attempt + 1} ---")
                print("Navigating to login page...")

                driver.get("https://bc38.atrieveerp.com/authenticationservice-Coquitlam/Account/Login?ReturnUrl=%2Fauthenticationservice-Coquitlam%2Fconnect%2Fauthorize%2Fcallback%3Fclient_id%3Ddotnetportalclient%26redirect_uri%3Dhttps%253A%252F%252Fbc38.atrieveerp.com%252Fcoquitlam%252Fpublic%252FExternalLogin.aspx%26response_type%3Dcode%2520id_token%26scope%3Dopenid%2520profile%2520offline_access%26state%3DNjM4Nzg3ODYzNTcyOTI3NDIzNTU0NjM0MTAx%26responseMode%3Dfragment%26nonce%3DNjM4Nzg3ODYzNTcyOTI3NDIzNTU0NjM0MTAx")

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
                print("✅ Login dashboard loaded.")
                print("Current URL:", driver.current_url)
                print("Page Title:", driver.title)

                print("Navigating to Job Shop page...")
                driver.get("https://bc38.atrieveerp.com/coquitlam/servlet/Broker?env=ads&template=ads.JobShop1.xml")

                WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
                print("✅ Table loaded successfully.")

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                table = soup.find('table', class_='table-striped')

                if table:
                    rows = table.find_all('tr')
                    if len(rows) > 1:
                        send_sms(f"📋 Records found! Number of rows: {len(rows) - 1}")
                    else:
                        print("📭 No new records found.")
                else:
                    send_sms("⚠️ Table not found on Job Shop page.")

                break  # Success — no more retries

            except (TimeoutException, NoSuchElementException, Exception) as e:
                print(f"Attempt {attempt + 1} failed: {repr(e)}")
                driver.save_screenshot(f"screenshot_attempt_{attempt + 1}.png")
                with open(f"page_source_attempt_{attempt + 1}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                if attempt == retry_count - 1:
                    send_sms("❌ Login failed after 3 attempts.")
                time.sleep(5)

    except Exception as e:
        print(f"\n🚨 Critical error: {repr(e)}")
        send_sms(f"Script failed: {repr(e)}")

    finally:
        if driver:
            driver.quit()

# ==== Run ====
check_for_table_records()

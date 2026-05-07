import json
import os

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

load_dotenv()

LOGIN = os.getenv('LOGIN')
PASSWORD = os.getenv('PASSWORD')

TARGET_COOKIES = [
    '.AspNet.Cookies',
    '.AspNet.CookiesC1',
    '.AspNet.CookiesC2',
    '__RequestVerificationToken_L0luc2NyaXB0aW9ucw2',
    'ASP.NET_SessionId',
    'LBServer'
]

def get_cookies_after_login(url, username, password):
    driver = webdriver.Chrome()

    try:
        driver.get(url)
        time.sleep(2) # Wait for page load

        # 1. Find the username field and type
        # Replace 'user_id_attribute' with the actual ID or Name from the site
        # 1. Handle the Email/Username field first (Microsoft usually splits these into two screens)
        email_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "loginfmt"))
        )
        email_field.send_keys(username)

        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "idSIButton9"))
        )
        next_button.click()


        password_field = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.NAME, "passwd"))
        )
        password_field.send_keys(password)

        # 3. Press Enter or click the login button
        sign_in_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "idSIButton9"))
        )
        sign_in_button.click()

        # Wait for the login to process and the dashboard to load
        time.sleep(20)

        # 4. Extract the cookies from the logged-in session
        all_cookies = driver.get_cookies()
        extracted_data = {}

        for cookie in all_cookies:
            if cookie['name'] in TARGET_COOKIES:
                extracted_data[cookie['name']] = cookie['value']

        # 5. Save to JSON 
        with open("uni_cookies.json", "w") as f:
            json.dump(extracted_data, f, indent=4)

        print(f"Done! Saved {len(extracted_data)} cookies to uni_cookies.json")

    finally:
        driver.quit()

# Usage
my_cookies = get_cookies_after_login("https://inscription.uni.lu/Inscriptions/Student/GuichetEtudiant/", LOGIN, PASSWORD)
print(my_cookies)
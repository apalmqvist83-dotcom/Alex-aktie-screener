from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def wake_streamlit_app(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(options=chrome_options)
    try:
        print(f"Besöker: {url}")
        driver.get(url)
        time.sleep(8)  # Vänta på att sidan laddas

        # Försök klicka på "Wake Up"-knappen om den finns
        try:
            wake_button = driver.find_element(By.XPATH, "//button[contains(., 'Wake up')] | //button[contains(., 'Wake')]")
            wake_button.click()
            print("✅ Klickade på Wake Up-knappen!")
            time.sleep(5)
        except:
            print("Ingen Wake Up-knapp hittades – appen var troligen redan vaken.")

        print("✅ Appen pingad framgångsrikt!")
    finally:
        driver.quit()

if __name__ == "__main__":
    APP_URL = "https://din-app-namn.streamlit.app/"   # ÄNDRA HÄR
    wake_streamlit_app(APP_URL)

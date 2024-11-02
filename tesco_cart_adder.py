from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import time
import undetected_chromedriver as uc


def setup_browser(chrome_driver_path='/bin/chromedriver'):
    service = Service(chrome_driver_path)
    options = Options()
    options.add_argument("--start-maximized")
    return uc.Chrome(service=service, options=options)


def tesco_log_in(browser, email, password):
    browser.get('https://secure.tesco.com/account/en-GB/login?from=/')
    
    try:
        email_field = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.NAME, 'email'))
        )
        email_field.clear()
        email_field.send_keys(email)

        password_field = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.NAME, 'password'))
        )
        password_field.clear()
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)

    except TimeoutException:
        print("Login fields took too long to load.")
    except Exception as e:
        print(f"An error occurred during login: {e}")


def add_product(browser, prod_id, quantity):
    browser.get(f'https://www.tesco.com/groceries/en-GB/products/{prod_id}')
    
    for _ in range(quantity):
        try:
            add_button = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'ddsweb-quantity-controls__add-button'))
            )
            add_button.click()
            time.sleep(0.4)

        except StaleElementReferenceException:
            print("Encountered StaleElementReferenceException, retrying...")
        except TimeoutException:
            print("Add button took too long to become clickable.")
            break


def tesco_add_all_products(browser, product_ids, quantities):
    start = time.time()
    
    for prod_id, quantity in zip(product_ids, quantities):
        add_product(browser, prod_id, quantity)
        
    elapsed = time.time() - start
    print(f"Total time elapsed for adding products: {elapsed:.2f} seconds.")
    print(f"Average time per item: {elapsed / len(product_ids):.2f} seconds.")


# Execution
browser = setup_browser()

tesco_log_in(browser, 'tescobrandtoothpaste@gmail.com', 'TescoMan!')
products = ['313610787', '312564080']
quantities = [2, 3]

tesco_add_all_products(browser, products, quantities)
time.sleep(10)
browser.close()
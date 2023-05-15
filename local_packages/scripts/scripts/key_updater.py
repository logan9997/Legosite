import time

import dotenv
from project_utils.general import General
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

GENERAL = General()


def update_ip(key):
    driver = webdriver.Chrome()
    url = 'https://www.bricklink.com/v2/api/register_consumer.page'
    driver.get(url)
    try:
        driver.find_element(
            By.XPATH, '''//*[@id='js-btn-save']/button[2]''').click()
    except:
        print('No cookies...')

    usernmame = 'frmUsername'
    password = 'frmPassword'
    button = 'blbtnLogin'

    driver.find_element(By.ID, usernmame).send_keys('loganbax101@gmail.com')
    driver.find_element(By.ID, password).send_keys('#Legomario1')
    driver.find_element(By.ID, button).click()

    time.sleep(3)

    delete_buttons = driver.find_elements(By.CLASS_NAME, 'deleteBtn')

    for button in delete_buttons:
        button.click()

    time.sleep(5)

    ip_inputs = driver.find_elements(By.CLASS_NAME, 'ipToken')
    ip_values = key.split('.')

    print(ip_values)

    time.sleep(5)

    for i, ip in enumerate(ip_inputs[:4]):
        print(i, ip)
        ip.send_keys(f'{ip_values[i]}')
        time.sleep(1.5)

    driver.find_element(By.ID, 'registIpBtn').click()

    time.sleep(3)

    token_value = driver.find_element(
        By.XPATH, '/html/body/div[3]/center/table/tbody/tr/td/div/table[3]/tbody/tr/td/div/table/tbody/tr[1]/td[2]').text
    token_secret = driver.find_element(
        By.XPATH, '/html/body/div[3]/center/table/tbody/tr/td/div/table[3]/tbody/tr/td/div/table/tbody/tr[2]/td[2]').text

    dotenv_file = GENERAL.configure_relative_file_path('.env', 10)
    dotenv.load_dotenv(dotenv_file)
    dotenv.set_key(dotenv_file, 'TOKEN_VALUE', token_value)
    dotenv.set_key(dotenv_file, 'TOKEN_SECRET', token_secret)

    driver.close()

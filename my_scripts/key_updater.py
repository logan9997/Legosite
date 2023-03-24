from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time




def update_ip(key):
    driver = webdriver.Chrome()
    url = "https://www.bricklink.com/v2/api/register_consumer.page"
    driver.get(url)
    try:
        driver.find_element(By.XPATH, """//*[@id="js-btn-save"]/button[2]""").click()
    except:
        print("No cookies...")

    usernmame = "frmUsername"
    password = "frmPassword"
    button = "blbtnLogin"

    driver.find_element(By.ID, usernmame).send_keys("loganbax101@gmail.com")
    driver.find_element(By.ID, password).send_keys("#Legomario1")
    driver.find_element(By.ID, button).click()

    time.sleep(3)

    delete_buttons = driver.find_elements(By.CLASS_NAME, "deleteBtn")

    for button in delete_buttons:
        button.click()

    time.sleep(5)

    ip_inputs = driver.find_elements(By.CLASS_NAME, "ipToken")
    ip_values = key.split(".")

    print(ip_values)

    time.sleep(5)

    for i, ip in enumerate(ip_inputs[:4]):
        print(i, ip)
        ip.send_keys(f"{ip_values[i]}")
        time.sleep(1.5)

    driver.find_element(By.ID, "registIpBtn").click()

    time.sleep(3)

    token_value = driver.find_element(By.XPATH, '/html/body/div[3]/center/table/tbody/tr/td/div/table[3]/tbody/tr/td/div/table/tbody/tr[1]/td[2]').text
    token_secret = driver.find_element(By.XPATH, '/html/body/div[3]/center/table/tbody/tr/td/div/table[3]/tbody/tr/td/div/table/tbody/tr[2]/td[2]').text

    with open("keys.txt", "r") as read_file:
        keys = [k.rstrip("\n") for k in read_file.readlines()]
    read_file.close()
    keys[2] = token_value
    keys[3] = token_secret

    with open("keys.txt", "w") as write_file:
        for k in keys:
            write_file.write(f"{k}\n")

    driver.close()


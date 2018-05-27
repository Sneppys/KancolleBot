"""Local tool used to update KC3 data."""
from selenium import webdriver
import os
import time

HOME_DIR = os.path.expanduser("~")

chrome_path = r"C:\chromedriver.exe"
local_data = os.path.join(HOME_DIR, r'AppData\Local\Google\Chrome\User Data')

opts = webdriver.ChromeOptions()
opts.add_argument('user-data-dir=' + local_data)
cap = opts.to_capabilities()

driver = webdriver.Chrome(desired_capabilities=cap,
                          executable_path=chrome_path)
driver.get("chrome-extension://hkgmldnainaglpjngpajnnjfhpdjkohh/"
           "pages/strategy/strategy.html")

time.sleep(1)
data = driver.execute_script('return window.localStorage.raw;')
driver.quit()

with open('../data.json', 'w', encoding='utf-8') as outfile:
    outfile.write(data)

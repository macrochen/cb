# -*- coding: utf-8 -*-

from selenium import webdriver


def get_chrome_driver(url, time_to_wait=10, options=webdriver.ChromeOptions()):
    # options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=options)
    driver.implicitly_wait(time_to_wait)
    # fixme 需要把chromedriver放到/usr/local/bin目录下
    if url is not None:
        driver.get(url)
    return driver


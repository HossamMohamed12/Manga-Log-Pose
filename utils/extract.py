import time
import os

from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def check_line_not_exists(filename, line_to_check):
    with open(filename, 'r') as file:
        for line in file:
            if line.strip() == line_to_check:
                return False  # Line exists in the file
    return True  # Line does not exist in the file


def locate_comick_starting_ch(manga_url: str, starting_ch):
    driver = Driver(uc=True, headless=True)
    processed_url = f'{manga_url}&date-order=0&chap-order=&chap={starting_ch}'
    driver.get(processed_url)
    # opening  manga chapter
    driver.execute_script("window.scrollTo(0, 1800)")
    time.sleep(1)

    try:
        ch_url = driver.find_element(By.XPATH,
                                     f"//span[text()='Ch. {starting_ch}']/parent::div/parent::a").get_attribute('href')
    except:
        reverse_ch = driver.find_element(By.XPATH, "//th//*[name()='svg']")
        actions = ActionChains(driver)
        actions.move_to_element(reverse_ch).click().perform()
        time.sleep(1)
        ch_url = driver.find_element(By.XPATH,
                                     f"//span[text()='Ch. {starting_ch}']/parent::div/parent::a").get_attribute('href')

    time.sleep(1)
    driver.get(ch_url)

    try:
        age_check = driver.find_element(By.XPATH, "//button[contains(text(),'View Page')]")
    except:
        age_check = None

    if age_check:
        age_check.click()

    return driver


def locate_mangafire_starting_ch(manga_url: str, starting_ch):
    driver = Driver(uc=True, headless=True, ad_block_on=True)
    driver.get(manga_url)

    ch_url = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                                   f'//div[@data-name="chapter"]//li[@data-number="{starting_ch}"]/a'))).get_attribute('href')
    time.sleep(1)
    print(ch_url)
    driver.get(ch_url)
    return driver

def get_comick_chapter_images(driver, number_of_downloads: int):
    txtfile = open('index_page.txt', 'w')
    img_links = {}
    start_page = 1
    i = 0
    while i < int(number_of_downloads):
        time.sleep(1)
        i += 1
        ch_images = driver.find_elements(By.XPATH, "//div[@class='relative']//img")
        link = driver.current_url
        link = link.split('-')[3:5]
        ch_number = ' '.join(link)
        img_links[ch_number] = [x.get_attribute('src') for x in ch_images]
        ch_pages_info = f'{ch_number} : {start_page} \n'
        print(ch_pages_info)
        if check_line_not_exists('index_page.txt', ch_pages_info):
            txtfile.write(ch_pages_info)
        start_page += len(ch_images)
        try:
            next_ch = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "(//a/button)[2]")))
        except:
            next_ch = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a/button")))
        next_ch.click()
        if driver.current_url == 'https://comick.io/home':
            break
    driver.close()
    txtfile.close()
    if os.path.isfile('../index_page.txt'):
        os.remove('../index_page.txt')
    os.rename('index_page.txt', '../index_page.txt')
    return img_links


def get_mangafire_chapter_images(driver, number_of_downloads: int):
    txtfile = open('index_page.txt', 'w')
    img_links = {}
    start_page = 1
    i = 0
    final_ch = driver.find_element(By.XPATH, "//b[@class='latest-number']").text
    while i < int(number_of_downloads):
        i += 1
        time.sleep(1)
        ch_images = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@id='page-wrapper']//img")))
        scroll_list = [ch_images[i] for i in range(len(ch_images)) if (i + 1) % 5 == 0]
        for img in scroll_list:
            ActionChains(driver).move_to_element(img).perform()
            time.sleep(.5)
        ch_images = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@id='page-wrapper']//img")))
        link = driver.current_url
        ch_number = (link.split('/')[-1]).replace('-',' ')
        img_links[ch_number] = [x.get_attribute('src') for x in ch_images]
        ch_pages_info = f'{ch_number} : {start_page} \n'
        print(ch_pages_info)
        if check_line_not_exists('index_page.txt', ch_pages_info):
            txtfile.write(ch_pages_info)
        start_page += len(ch_images)
        current_ch = driver.find_element(By.XPATH, "//b[@class='current-number']").text
        if current_ch == final_ch:
            break
        next_ch_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[@class='next']")))
        driver.execute_script("arguments[0].click();", next_ch_button)
    driver.close()
    txtfile.close()
    if os.path.isfile('../index_page.txt'):
        os.remove('../index_page.txt')
    os.rename('index_page.txt', '../index_page.txt')
    return img_links

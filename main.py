import os
import time
import itertools
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import csv

def scrape_phone_links(driver,url):
    driver.get(url)
    # get the javascript with the phone list from this xpath
    info = driver.find_element_by_xpath("//main[@id='MainContent']/div/script[1]")
    info_string = info.get_attribute('innerHTML')
    # find all iphone names from the javascript file in the info web element
    import re
    regex = r'\"name":\"(.*?)\"'
    devices = re.findall(regex, info_string)

    # filter iphone models
    phone_models = []
    for device_name in devices:
        if 'iphone' in device_name.lower():
            iphone = str(device_name).replace(' ', '-').lower()
            # to seperate number and letters that are together
            iphone = re.sub(r'(?<=\d)(?=[^\d\s])|(?<=[^\d\s])(?=\d)', '-', iphone)
            iphone = iphone.replace('--', '-')
            if 'original' in iphone:
                iphone = iphone.replace('original-', '')
            if 'iphone-3-g' in iphone:
                phone_models.append('iphone-3-g')
                phone_models.append('iphone-3-g-s')
                continue
            phone_models.append(iphone)
    print(phone_models)
    return phone_models

def scrape_data(driver,url,power_on=True,screen_light_up=True,screen_cracks=False,first_scrape=False):
    full_url = url
    driver.get(full_url)
    yes_condition = driver.find_elements_by_xpath("//span[contains(text(),'Yes')]")
    no_condition = driver.find_elements_by_xpath("//span[contains(text(),'No')]")

    if power_on:
        yes_condition[0].click()
    else:
        no_condition[0].click()
    if screen_light_up:
        yes_condition[1].click()
    else:
        no_condition[1].click()
    if screen_cracks:
        yes_condition[2].click()
    else:
        no_condition[2].click()
    if first_scrape:
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//*[@data-tracking-id='regional-no']"))).click()
        except Exception as e:
            print(e)
            print('error in first_scrape')
    driver.implicitly_wait(5)
    WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH, "//*[@alt='edit']")))


    try:
        return driver.find_element_by_xpath('//sup/ancestor::h4').text
    except:
        return "0"

def main():
    #setting up selenium chrome driver
    chrome_options = webdriver.ChromeOptions()
    preferences = {"safebrowsing.enabled": True}
    chrome_options.add_experimental_option("prefs", preferences)

    #chromedriver.exe located in the same directory
    driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=os.getcwd() + "\\chromedriver.exe")

    try:
        original_url = 'https://www.ecoatm.com/a/devices/apple'
        phone_models = scrape_phone_links(driver,original_url)
        csv_columns = ['model','carrier','price', 'power_on', 'screen_light_up', 'screen_cracks']

        file_exists = os.path.isfile(f'{os.getcwd()}\\data.csv')
        with open(f'{os.getcwd()}\\data.csv','a',newline='') as csvfile:
            fieldnames = ['Model','MemorySize','CarrierName','Price','PowerOn','ScreenLightUpCorrectly','CracksAnywhere']
            writer = csv.DictWriter(csvfile,fieldnames = fieldnames)

            if not file_exists:
                writer.writeheader()

            for models in phone_models:
                new_url = f'{original_url}/{models}'
                carrier_list = ['cricket','sprint','us-cellular','at-t','other','verizon','t-mobile','metropcs','unlocked']
                try:
                    driver.get(new_url)
                    first_scrape = True
                    memory_size_element = driver.find_elements_by_xpath("//div[contains(@class,'MuiGrid-root MuiGrid-container')]/div/button/span/div/span")
                    memory_size = []
                    for size_element in memory_size_element:
                        memory_size.append(str(size_element.text).lower())

                    model = driver.find_element_by_xpath("//div[contains(text(),'iPhone')]").text

                    #crawling through each page and scraping the data into a list of dictionary
                    for size in memory_size:
                        try:
                            for carrier in carrier_list:
                                try:
                                    scrape_url = f'{new_url}/{size}/{carrier}'
                                    device_state = ['power_on', 'screen_light_up', 'screen_cracks']
                                    device_state_combination = [list(zip(device_state, x)) for x in itertools.product([True, False], repeat=len(device_state))]
                                    for dev_state in device_state_combination:
                                        try:
                                            power_on = dev_state[0][1];screen_light_up =dev_state[1][1];screen_cracks=dev_state[2][1]
                                            price = scrape_data(driver,scrape_url,power_on=power_on,screen_light_up=screen_light_up,screen_cracks=screen_cracks,first_scrape=first_scrape)
                                            print(f'{model}|{size}|{carrier}|{price}|{power_on}|{screen_light_up}|{screen_cracks}')
                                            first_scrape = False
                                            try:
                                                writer.writerow({
                                                    'Model' : str(model),
                                                    'MemorySize': str(size),
                                                    'CarrierName':str(carrier),
                                                    'Price':str(price),
                                                    'PowerOn':str(power_on),
                                                    'ScreenLightUpCorrectly':str(screen_light_up),
                                                    'CracksAnywhere':str(screen_cracks)})
                                            except Exception as e:
                                                print(e)
                                        except Exception as e:
                                            print(e);print('error in : dev_state')
                                except Exception as e:
                                    print(e);print('error in : carrier')
                        except Exception as e:
                            print(e);print('error in : size')
                except Exception as e:
                    print(e);print('error in : phone_models')

    except Exception as e:
        print(e);print('error in url')

    driver.close()

if __name__ == "__main__":
    main()
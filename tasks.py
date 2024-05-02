from robocorp.tasks import task, teardown
from robocorp import workitems
import logging
import time
import os
from output.news import News
from output.dates_processor import DatesProcessor
from RPA.HTTP import HTTP
from RPA.Excel.Files import Files
import requests
from RPA.Excel.Files import Files
from RPA.Browser.Selenium import Selenium

selenium = Selenium()
excel = Files()
http = HTTP()

# elements locators
search_icon = "//button[@class='SearchOverlay-search-button']"
search_input_field = "//input[@placeholder='Keyword Search...']"
sort_news_list = "//select[@class='Select-input']"
news_title_elems = "//div[@class='PageList-items-item']//div[@class='PagePromo']//div[@class='PagePromo-content']//bsp-custom-headline//div[@class='PagePromo-title']//a/span"

# main params
search_phrase = None
required_months_count = 0
news_list = []

@task
def extract_news():
    define_search_params()
    open_news_site()
    filter_news(search_phrase)
    sort_news_by_newest()
    collect_news_info()
    create_excel_file(news_list)


def define_search_params():
    key_params = workitems.inputs.current.payload
    global search_phrase
    search_phrase = key_params["search_phrase"]
    global required_months_count
    required_months_count = key_params["required_month_count"]


def open_news_site():
    selenium.open_chrome_browser("https://apnews.com/")
    selenium.maximize_browser_window()
    selenium.set_selenium_implicit_wait(30)
    logging.info("News website opened")


def filter_news(phrase):
    selenium.wait_until_element_is_visible(search_icon)
    selenium.click_element(search_icon)
    selenium.wait_until_element_is_visible(search_input_field)
    selenium.input_text(search_input_field, phrase)
    time.sleep(2)
    selenium.press_keys(None, "RETURN")
    logging.info("News filtered by key phrase")
    time.sleep(5)


def sort_news_by_newest():
    selenium.wait_until_element_is_visible(sort_news_list)
    selenium.select_from_list_by_label(sort_news_list, "Newest")
    logging.info("News sorted by newest")
    time.sleep(10)


def download_news_image(img_url, path_to_save, image_name):
    img_data = requests.get(img_url).content
    with open(f'{path_to_save}/{image_name}', 'wb') as handler:
        handler.write(img_data)


def get_news_object(title, date, description, image_name, search_phrase):
    occurrences = title.lower().count(search_phrase.lower()) + description.lower().count(search_phrase.lower())
    money_signs = ["$", "dollar", "usd"]
    money_in_title_description = any(money_sign in title for money_sign in money_signs) or any(money_sign in description for money_sign in money_signs)
    return News(title, date, description, image_name, occurrences, money_in_title_description)


def collect_news_info():
    selenium.set_selenium_implicit_wait(2)
    news_count = selenium.get_element_count(news_title_elems) - 1
    for i in range(news_count):
        news_title_elem = get_title_elem(i)
        news_description_elem = get_description_elem(i)
        news_date_elem = get_date_elem(i)
        time.sleep(2)
        news_date = selenium.get_text(news_date_elem)  
        date_suitable = DatesProcessor(required_months_count).is_suitable_date(news_date)
        if not date_suitable: continue
        time.sleep(2)
        news_title = selenium.get_text(news_title_elem)
        time.sleep(2)
        news_description = selenium.get_text(news_description_elem)
        time.sleep(2)
        image_name = f"image_news_{i+1}.jpg"
        try:
            news_image_elem = selenium.get_webelement(f"//bsp-list-loadmore//div[2]//div[{i+1}]//div//div[1]//a//picture/img")
            img_download_url = selenium.get_element_attribute(news_image_elem, "src")
            download_news_image(img_download_url, "output/images", image_name)
        except Exception as e:
            image_name = "Image absent"
            print(e)
        news_object = get_news_object(news_title, news_date, news_description, image_name, search_phrase)
        news_list.append(news_object)
    logging.info("News titles and descriptions obtained, images downloaded")


def get_title_elem(i):
    elem = None
    try:
        elem = selenium.get_webelement(f"//bsp-list-loadmore//div[2]//div[{i+1}]//div//div[2]//bsp-custom-headline//div//a/span")
    except Exception as e:
        elem = selenium.get_webelement(f"//bsp-list-loadmore//div[2]//div[{i+1}]//div//div//bsp-custom-headline//div//a/span")
    return elem


def get_description_elem(i):
    descriptions_elems = selenium.get_webelements("//div[@class='PageList-items-item']//div[@class='PagePromo']//div[@class='PagePromo-content']//div[@class='PagePromo-description']//a/span")
    needed_elem = descriptions_elems[i]
    return needed_elem


def get_date_elem(i):
    elem = None
    try:
        elem = selenium.get_webelement(f"//bsp-list-loadmore//div[2]//div[{i+1}]//div//div[2]//div[2]//div//bsp-timestamp/span")
    except Exception as e:
        elem = selenium.get_webelement(f"//bsp-list-loadmore//div[2]//div[{i+1}]//div//div//div[2]//div//bsp-timestamp/span")
    return elem


def create_excel_file(news):
    excel_data = []
    for item in news:
        excel_data.append(item.__dict__)
    excel.create_workbook()
    excel.create_worksheet(name="News Info",content=excel_data,header=True)
    excel.remove_worksheet("Sheet")
    excel.save_workbook("./output/News Summary.xlsx")
    logging.info("XLSX file with news summary has been created")


@teardown(scope="task")
def after_each(task):
    selenium.screenshot(None, "output/screenshot.png")
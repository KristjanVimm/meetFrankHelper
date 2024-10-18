import time
import json
import datetime
import os.path as op
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def create_paths():
    date = datetime.date.today()
    week_number = str(date.isocalendar().week)
    day_number = str(date.isocalendar().weekday)
    date_snippet = f'{week_number}_{day_number}'
    all_offers_path = op.join(op.dirname(op.abspath(__file__)), 'meetFrank_files', 'all_offers',
                              'all_offers_' + date_snippet + '.json')
    my_offers_path = op.join(op.dirname(op.abspath(__file__)), 'meetFrank_files', 'my_offers', 'my_offers_' + date_snippet + '.json')
    return all_offers_path, my_offers_path


def write_to_json(offers_dict, path):
    offers_json = json.dumps(offers_dict, indent=2)
    with open(path, "w") as outfile:
        outfile.write(offers_json)


def specify_driver_options(url):
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-position=-2400,-2400")  # remove this line once -headless=new works again
    chrome_options.add_argument("--disable-search-engine-choice-screen")
    chrome_options.add_argument("--window-size=1450,798")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    return driver


def gather_offer_htmls(driver, offers_html):
    html = driver.page_source
    soup = BeautifulSoup(html, features='html.parser')
    offers_html.update(soup.find('div', class_='c0 c2').find_all('div', recursive=False))
    print(len(offers_html))


def scroll_for_offers(driver, repetitions, seconds):
    # scroll down until there are no more products to load
    offers_html = set()
    last_position = driver.execute_script('return window.pageYOffset;')
    for i in range(1, repetitions):
        gather_offer_htmls(driver, offers_html)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(seconds)
        current_position = driver.execute_script('return window.pageYOffset;')
        if current_position == last_position:
            break
        last_position = current_position
    return list(offers_html)


def get_soup_meetfrank(url_snippet):
    driver = specify_driver_options(url_snippet)
    offers_html = scroll_for_offers(driver, repetitions=1000, seconds=2)
    driver.quit()
    return offers_html


def extract_from_offer(global_url, offer, all_offers_dict, my_offers_dict):
    url = global_url + offer.find('a')['href']
    title = offer.find('h2').text.strip().lower()
    company = offer.find('span').text.strip()
    all_offers_dict[url] = [title, company]
    if any(snippet in title for snippet in ['senior', 'vanem', 'sr.', 'sr ', 'lead', 'manager']):
        return None
    if any(snippet in title for snippet in ['junior', 'jr.']):
        print('\n JUNIOR!! \n')
    print([title, company, url])
    my_offers_dict[url] = [title, company]


def get_relevant_offers(categories):
    all_offers_path, my_offers_path = create_paths()
    global_url = 'https://meetfrank.com'
    offers_html = []
    for category_url in categories:
        offers_from_category = get_soup_meetfrank(global_url + category_url)
        offers_html.extend(offers_from_category)
        print(f'category {categories.index(category_url)} end')
    offers_html = [elem for elem in offers_html if elem.find('a')]
    all_offers_dict = {}
    my_offers_dict = {}
    for offer in offers_html:
        extract_from_offer(global_url, offer, all_offers_dict, my_offers_dict)
    print(str(len(all_offers_dict)) + ' - nr of all offers')
    print(str(len(my_offers_dict)) + ' - nr of my offers')
    write_to_json(all_offers_dict, all_offers_path)
    write_to_json(my_offers_dict, my_offers_path)


get_relevant_offers(['/latest-remote-software-engineering-jobs-in-estonia', '/latest-remote-it-and-sysadmin-jobs-in-estonia',
                     '/latest-remote-data-analytics-jobs-in-estonia'])

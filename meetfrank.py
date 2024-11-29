import time
import json
import datetime
import os.path as op
from os import listdir
from operator import itemgetter
from os.path import isfile, join
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def create_paths():
    date = datetime.date.today()
    year_last_two_numbers = str(date.isocalendar().year)[2:]
    week_number = str(date.isocalendar().week)
    day_number = str(date.isocalendar().weekday)
    date_snippet = f'{year_last_two_numbers}_{week_number}_{day_number}'
    all_offers_path = op.join(op.dirname(op.abspath(__file__)), 'meetFrank_files', 'all_offers',
                              'all_offers_' + date_snippet + '.json')
    my_offers_path = op.join(op.dirname(op.abspath(__file__)), 'meetFrank_files', 'my_offers', 'my_offers_' + date_snippet + '.json')
    # getting most recent alltime_offers filepath
    alltime_offers_dir_path = op.join(op.dirname(op.abspath(__file__)), 'meetFrank_files', 'alltime_offers')
    onlyfiles = [f for f in listdir(alltime_offers_dir_path) if isfile(join(alltime_offers_dir_path, f))]
    onlydates = [file_name.split('.')[0].split('_')[2:5] for file_name in onlyfiles]
    sorted_dates = sorted(onlydates, key=itemgetter(0, 1, 2))
    most_recent_date = sorted_dates[-1]
    most_recent_file = [e for e in onlyfiles if '_'.join(most_recent_date) in e][0]
    old_alltime_offers_path = op.join(op.dirname(op.abspath(__file__)), 'meetFrank_files', 'alltime_offers', most_recent_file)
    new_alltime_offers_path = op.join(op.dirname(op.abspath(__file__)), 'meetFrank_files', 'alltime_offers',
                                      'alltime_offers_' + date_snippet + '.json')
    if old_alltime_offers_path == new_alltime_offers_path:
        should_continue = input("You already scraped today, continuing would overwrite the files. Do you want to continue? y | n ")
        if should_continue == "n":
            raise SystemExit(0)
    return all_offers_path, my_offers_path, old_alltime_offers_path, new_alltime_offers_path


def read_previous(path):
    with open(path, 'r') as openfile:
        contents = json.load(openfile)
    return contents


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
    offers_html.update(soup.find('div', class_='c6 c8').find_all('div', recursive=False))
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


def get_offer_htmls(url_snippet, message):
    driver = specify_driver_options(url_snippet)
    offers_html = scroll_for_offers(driver, repetitions=1000, seconds=2)
    driver.quit()
    print(message)
    return offers_html


def extract_from_offer(global_url, offer, all_offers_dict, my_offers_dict, previous_offers, alltime_offers):
    url = global_url + offer.find('a')['href']
    title = offer.find('h2').text.strip().lower()
    company = offer.find('span').text.strip()
    if url in list(previous_offers.keys()):
        return None
    alltime_offers[url] = [title, company]
    all_offers_dict[url] = [title, company]
    if any(snippet in title for snippet in ['senior', 'seenior', 'vanem', 'sr.', 'sr ', 'lead', 'manager']):
        return None
    if any(snippet in title for snippet in ['junior', 'jr.']):
        print('\n JUNIOR!! \n')
    print([title, company, url])
    my_offers_dict[url] = [title, company]


def final_print_and_write(new_alltime_offers, all_offers_dict, my_offers_dict, new_alltime_offers_path, all_offers_path, my_offers_path):
    print(str(len(new_alltime_offers)) + ' - nr of alltime offers')
    print(str(len(all_offers_dict)) + ' - nr of all offers')
    print(str(len(my_offers_dict)) + ' - nr of my offers')
    write_to_json(new_alltime_offers, new_alltime_offers_path)
    write_to_json(all_offers_dict, all_offers_path)
    write_to_json(my_offers_dict, my_offers_path)


def meet_frank_main():
    categories = ['/latest-remote-software-engineering-jobs-in-estonia', '/latest-remote-it-and-sysadmin-jobs-in-estonia',
                  '/latest-remote-data-analytics-jobs-in-estonia']
    all_offers_path, my_offers_path, alltime_offers_path, new_alltime_offers_path = create_paths()
    global_url = 'https://meetfrank.com'
    previous_offers = read_previous(alltime_offers_path)
    offers_html = []
    for category_url in categories:
        offers_from_category = get_offer_htmls(global_url + category_url, f'category {categories.index(category_url)} end')
        offers_html.extend(offers_from_category)
    offers_html = [elem for elem in offers_html if elem.find('a')]
    alltime_offers_dict, all_offers_dict, my_offers_dict = {}, {}, {}
    for offer in offers_html:
        extract_from_offer(global_url, offer, all_offers_dict, my_offers_dict, previous_offers, alltime_offers_dict)
    new_alltime_offers = previous_offers | alltime_offers_dict
    final_print_and_write(new_alltime_offers, all_offers_dict, my_offers_dict, new_alltime_offers_path, all_offers_path, my_offers_path)


if __name__ == "__main__":
    meet_frank_main()

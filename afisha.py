import json
import logging
import subprocess
import time
import os
import shutil
from os import listdir
from os.path import isfile, join
from pathlib import Path

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent


def get_url_to_data(start_url):
    user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                  ' AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/111.0.0.0 Safari/537.36')

    caps = DesiredCapabilities.CHROME
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}

    options = Options()
    #options.add_argument("--headless")
    options.add_argument(f'--user-agent={user_agent}')

    driver = webdriver.Chrome(desired_capabilities=caps, options=options)

    try:
        driver.get(url=start_url)
        time.sleep(15)

        def process_browser_log_entry(entry):
            response = json.loads(entry['message'])['message']
            return response

        browser_log = driver.get_log('performance')
        events = [process_browser_log_entry(entry) for entry in browser_log]
        url_to_data = []
        for event in events:
            get_params = event.get('params')
            if 'Network.response' in event['method'] and get_params is not None:
                get_response = get_params.get('response')
                if get_response is not None:
                    get_url = get_response.get('url')
                    if get_url is not None:
                        if 'https://widget.afisha.yandex.ru/api/mds?key' in get_url:
                            url_to_data.append(get_url)

        get_data(url_to_data)

    except Exception as e:
        logger.error(f"Возникла ошибка {e}")
    finally:
        driver.close()
        driver.quit()


def reqests_to_url(url: str, return_json: bool = None):
    try:
        response = requests.get(url)
        if response.status_code >= 400 and response.status <= 500:
            logger.error(f"Возникла ошибка клиента {response.status}")
        elif response.status_code >= 500:
            logger.error(f"Возникла ошибка сервера {response.status}")
        else:
            if return_json:
                return response.json()
            return response.text
    except requests.Timeout as e:
        logger.error(f"Возникла ошибка(Timeout) {e}")
    except Exception as e:
        logger.error(f"Возникла ошибка {e}")


def get_data(list_url):
    for url in list_url:
        if url[-1] == '3':
            with open('svg.json', 'w', encoding='utf-8') as f:
                f.write(str(reqests_to_url(url)))
        else:
            with open('seats.json', 'w', encoding='utf-8') as f:
                f.write(reqests_to_url(url))


if __name__ == '__main__':
    get_url_to_data(str(input("Введите url: ")))
    venue_scheme = str(input("Введите venue: "))
    name_scheme = str(input("Введите название схемы: "))

    dir_export_old = BASE_DIR.joinpath('export_old')
    if not os.path.exists(dir_export_old):
        os.makedirs(dir_export_old)

    dir_export = BASE_DIR.joinpath('export')
    files_json = [f for f in listdir(dir_export) if isfile(join(dir_export, f))]
    if len(files_json) > 0:
        for file_json in files_json:
            path_file_json = dir_export.joinpath(file_json)
            try:
                shutil.move(path_file_json, dir_export_old)
            except Exception as error:
                print(error)
                file_is_exists = dir_export_old.joinpath(file_json)
                os.remove(file_is_exists)
                shutil.move(path_file_json, dir_export_old)

    file_main = BASE_DIR.joinpath('converter.exe')
    subprocess.call(file_main)

    dir_export = BASE_DIR.joinpath('export')
    files_json = [f for f in listdir(dir_export) if isfile(join(dir_export, f))]
    json_file = dir_export.joinpath(files_json[0])
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = f.read()

    final_json = json.loads(json_data)
    r_add = requests.post(
        'http://193.178.170.180/api/add_scheme/',
        json=final_json
    )
    r_set_venue = requests.post(
        'http://193.178.170.180/api/set-venue/',
        json={
            "name": name_scheme,
            "venue": venue_scheme
        }
    )
    if (r_add.status_code == 200) and (r_set_venue.status_code == 200):
        print('Схема отпрвленна')
    if r_add.status_code != 200:
        print('Возникла ошибка с добавлением схемы')
    if r_set_venue.status_code != 200:
        print('Возникла ошибка с изменением venue')
    time.sleep(10)

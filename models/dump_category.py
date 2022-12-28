import json
import os

import requests

from config.settings import settings

categories = {'id': [], 'name': [], 'nameEn': [], 'parentId': []}

# Config
logger = settings.logger
products_url = settings.products_url
category_url = settings.category_url + settings.ecwid_token
headers = settings.ecwid_headers


def dump_categories():

    # Creating a Get request for categories
    products_response = requests.get(products_url, headers=headers).json()
    pages = int(products_response['total'])
    

    # Pulling categories data and storing them in a list
    for offset in range(0, pages, 100):
        category_response = requests.get(category_url + '&offset=' + str(offset)).json()
        items_list = category_response['items']

        # Loading primary categories info
        for value in items_list:
            try:
                if 'id' in categories:
                    if categories['id'] != value['id']:
                        categories['id'].append(value['id'])
                        categories['name'].append(value['nameTranslated']['ar'])
                        categories['nameEn'].append(value['nameTranslated']['en'])                        
                        categories['parentId'].append(value['parentId'])
            except KeyError as e:
                categories['parentId'].append(None)
                pass
                    
    logger.info("Category dump is successfull")
    return categories


def check_category():
    global categories
    File_path = 'dumps/categories.json'
    if os.path.exists(File_path):
        request_category = requests.get(category_url, headers=headers).json()
        category_total = int(request_category['total'])
        # Dumping categories into a dict var
        open_json = open('dumps/categories.json', encoding='utf-8')
        categories = json.load(open_json)
        if len(categories['name']) == category_total:
            pass
        else:
            from threading import Thread
            new_thread = Thread(target=dump_categories)
            new_thread.start()
            new_thread.join()
            with open(File_path, 'w', encoding='utf-8') as file:
                file.truncate()
                json.dump(categories, file, ensure_ascii=False)
            file.close()
    else:
        from threading import Thread
        new_thread = Thread(target=dump_categories)
        new_thread.start()
        new_thread.join()
        with open(File_path, 'w', encoding='utf-8') as file:
            json.dump(categories, file, ensure_ascii=False)
        file.close()
        
    return categories
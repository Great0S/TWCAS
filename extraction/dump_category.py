import json
import logging
import os
import requests
from logging import config

from config.logger import log_config

config.dictConfig(log_config)
logger = logging.getLogger('mainLog')
categories = {'id': [], 'name': [], 'nameEn': [], 'parentId': []}
eurl = "https://app.ecwid.com/api/v3/63690252/products"
curl = "https://app.ecwid.com/api/v3/63690252/categories?token=secret_4i936SRqRp3317MZ51Aa4tVjeUVyGwW7"
eheaders = {
    "Authorization": "Bearer secret_4i936SRqRp3317MZ51Aa4tVjeUVyGwW7",
    "Content-Type": 'application/json;charset: utf-8'
}


def dump_categories():

    # Creating a Get request for categories
    r1 = requests.get(eurl, headers=eheaders).json()
    pages = int(r1['total'])
    

    # Pulling categories data and storing them in a list
    for offset in range(0, pages, 100):
        r2 = requests.get(curl + '&offset=' + str(offset)).json()
        items_list = r2['items']

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
    File_path = 'extraction/categories.json'
    if os.path.exists(File_path):
        request_category = requests.get(curl, headers=eheaders).json()
        category_total = int(request_category['total'])
        # Dumping categories into a dict var
        open_json = open('extraction/categories.json', encoding='utf-8')
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
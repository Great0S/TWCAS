
import re
from models.dump_category import check_category


categories = check_category()
telegram_category = 'قمصان  وبلايز'
for value in categories:
    for item in value:
        words = re.split("\s", telegram_category)
        if telegram_category == item['nameTranslated']['ar']:
            if 'parentId' in item:
                if item['parentId'] == 127443592:
                    default_category_name = telegram_category
                    default_category_name_en = item['name']
                    default_category_ID = item['id']
                    break
                else:
                    continue
        elif telegram_category != item['nameTranslated']['ar']:
            for word in words:
                if re.search(f"^{word}\s[أ-ي]+|^[أ-ي]+\s{word}", item['nameTranslated']['ar']) and word != '':
                    if 'parentId' in item:
                        if item['parentId'] == 127443592:
                            default_category_name = item['nameTranslated']['ar']
                            default_category_name_en = item['name']
                            default_category_ID = item['id']
                            break
                        else:
                            continue
            
    
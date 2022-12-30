import json
import re

import requests

from config.settings import settings
from models.category_filling import category_fill
from models.category_processor import category_processor
from models.options_processor import options_fill
from models.text_processor import text_processor
from tasks.checks import clear_all
from app.celery_server import celery

logger = settings.logger
arabic_translate = settings.arabic_translate


# Creates a product and assign the main product image
@celery.task()
def create_product(message, MCategory, categories, media_path):
    global ResContent, Main, body, seoNameEn
    main_category = main_category_en = None
    
    # Checking message type
    if message:
        try:
            # Text processing
            RefinedTxt = text_processor(message)

            # Condition to check for invalid message length
            if len(RefinedTxt) < 7:
                clear_all(media_path)
                logger.error(
                    f"Invalid message length found | Length: {len(RefinedTxt)}"
                )
                return

            # Creating variables with ready to use data from telegram message
            name = RefinedTxt[1].strip()
            nameEn = arabic_translate.translate(name)
            nameEn = re.sub('a ', '', nameEn)
            nameEn = nameEn.capitalize()
            # Checking for invalid criteria
            if re.search('السيري', name) or re.search('السيري', name):
                clear_all(media_path)
                logger.error(
                    'Invalid name found')
                return

            size = RefinedTxt[2]
            size = re.sub('\D', '', size)
            pcQty = RefinedTxt[3]
            pcQty = int(re.sub('\D', '', pcQty))
            price = RefinedTxt[4]
            price = float(re.sub('[^\d|^\d.\d]', '', price))
            pcPrice = RefinedTxt[5]
            pcPrice = int(re.sub('\D', '', pcPrice))
            sku = RefinedTxt[6]
            if re.search('-', sku):
                sku = sku.replace("كود الموديل", "")
                sku = sku.replace('-', '')
                sku = sku.split()
                sku = str(sku[1]) + '-' + str(sku[0])
            else:
                sku = re.sub('[^a-zA-Z\d\-]', '', sku)
            true = True
            false = False

            # Category values
            telegram_category = RefinedTxt[0].strip()
            if re.search('ماركه', telegram_category) or re.search('ماركة', telegram_category):
                clear_all(media_path)
                logger.warning(
                    f'Brand found with sku: {sku}')
                return
            
            main_category, main_category_en = category_processor(
                telegram_category, main_category, categories)

            # Options values
            OpValues = [2, 3, 5]
            OpBody = []

            # Extract options from processed text
            options_fill(RefinedTxt, false, OpValues, OpBody)
            # Assigning categories using a for loop and a condition to match stored category list
            category_ids, main_category_id, category_json = category_fill(
                main_category, categories, MCategory)

            # Create a product request body   
            if main_category_en:         
                seoNameEn = main_category_en + ' / ' + nameEn
            else:
                seoNameEn = nameEn
                
            if main_category_en:     
                seoName = main_category + ' / ' + name
            else:
                seoName = name
            
            body = {
                "sku": sku,
                "unlimited": true,
                "inStovalue": true,
                "name": nameEn,
                "nameTranslated": {
                    "ar": name,
                    "en": nameEn
                },
                "price": price,
                "enabled": true,
                "options": OpBody,
                "description": "<b>Choose the best products from hundreds of Turkish high-end brands. We offer you the largest selection of Turkish clothes and the latest trends in women's, men's and children's fashion that suit all tastes. In different sizes and colors.</b>",
                "descriptionTranslated": {
                    "ar": "<b>اختار/ي أفضل المنتجات من مئات الماركات الراقية التركية. نقدم لك/ي أكبر تشكيلة    من الملابس التركية واحدث الصيحات في الأزياء النسائية والرجالية والاطفال التي تناسب جميع الأذواق.   بمقاسات وألوان مختلفة.</b>",
                    "en": "<b>Choose the best products from hundreds of Turkish high-end brands. We offer you the largest selection of Turkish clothes and the latest trends in women's, men's and children's fashion that suit all tastes. In different sizes and colors.</b>"
                },
                "categoryIds": category_ids,
                "categories": category_json,
                "defaultCategoryId": main_category_id,
                "seoTitle": f'{seoNameEn}',
                "seoTitleTranslated": {
                    "ar": seoName,
                    "en": seoNameEn
                },
                "seoDescription": "Choose the best products from hundreds of Turkish high-end brands. We offer you the largest selection of Turkish clothes and the latest trends in women's, men's and children's fashion that suit all tastes. In different sizes and colours.",
                "seoDescriptionTranslated": {
                    "ar": "اختار/ي أفضل المنتجات من مئات الماركات الراقية التركية. نقدم لك/ي أكبر تشكيلة    من الملابس التركية واحدث الصيحات في الأزياء النسائية والرجالية والاطفال التي تناسب جميع الأذواق.   بمقاسات وألوان مختلفة.",
                    "en": "Choose the best products from hundreds of Turkish high-end brands. We offer you the largest selection of Turkish clothes and the latest trends in women's, men's and children's fashion that suit all tastes. In different sizes and colours."
                },
                "attributes": [{"name": "Note", "nameTranslated": {"ar": "ملاحظة", "en": "Note"},
                                "value": "The choice of colors is done at the start of processing the order.",
                                "valueTranslated": {
                    "ar": "اختيار الألوان يتم عند البدء بتجهيز الطلبية",
                          "en": "The choice of colors is done at the start of processing the order."
                }, "show":   "DESCR", "type": "UPC"}, {"name": "Brand", "nameTranslated": {"ar": "العلامة التجارية", "en": "Brand"},
                                                       "value": "Al Beyan Fashion™",
                                                       "valueTranslated": {
                    "ar": "Al Beyan Fashion™",
                    "en": "Al Beyan Fashion™"
                }, "show":   "DESCR", "type": "BRAND"}],
                "subtitle": "The displayed price is for the full set",
                "subtitleTranslated": {
                    "ar": "السعر المعروض للسيري كامل",
                    "en": "The displayed price is for the full set"
                }
            }

            # Parsing collected data
            ResContent, resCode = poster(body)
            # Feedback and returning response and media_path new values
            if resCode == 200:
                # Created product ID
                if 'id' in ResContent:
                    ItemId = ResContent['id']
                    logger.info(
                        f"Product created successfully with ID: {ItemId} | SKU: {sku}"
                    )
                    return ItemId
                else:
                    logger.error(
                        f"Product ID is empty?! | Response: {ResContent} | Sku: {sku}")
                    return ItemId

            elif resCode == 400:
                logger.error(
                    f"New product body request parameters are malformed | Sku: {sku} | Error Message: {ResContent['errorMessage']} | Error code: {ResContent['errorCode']}"
                )
                clear_all(media_path)
                return None
            elif resCode == 409:
                logger.warning(
                    f"SKU_ALREADY_EXISTS: {sku} | Error Message: {ResContent['errorMessage']} | Error code: {ResContent['errorCode']}"
                )
                clear_all(media_path)
                return None
            else:
                logger.info(
                    f"Failed to create a new product")
                clear_all(media_path)
                return None

        # Errors handling
        except IndexError as e:
            logger.exception(e)
            return None

        except KeyError as e:
            logger.exception(e)
            return None

        except ValueError as e:
            logger.exception(e)
            return None

def poster(body):

    # Sending the POST request to create the products
    postData = json.dumps(body)
    response = requests.post(settings.products_url, data=postData, headers=settings.ecwid_headers)
    resCode = int(response.status_code)
    response = json.loads(response.text.encode('utf-8'))
    logger.info("Body request has been sent")
    return response, resCode
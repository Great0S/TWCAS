from __future__ import absolute_import

import json
import os
import re
import glob

import magic
import logging
from logging import config
import requests
from moviepy.editor import VideoFileClip
from deep_translator import GoogleTranslator

from config.logger import log_config
from processors.category_filling import category_fill
from processors.category_processor import category_processor
from processors.options_processor import options_fill
from processors.text_processor import text_processor

# Declaring global variables
config.dictConfig(log_config)
logger = logging.getLogger('mainLog')
ts = GoogleTranslator(source='ar', target='en')
payload = {}
headers = {
    "Authorization": "Bearer secret_4i936SRqRp3317MZ51Aa4tVjeUVyGwW7",
    "Content-Type": 'application/json;charset: utf-8'
}
cheaders = {
    'Content-Type': 'application/json;charset=utf-8',
    'Accept-Encoding': 'gzip'
}
eurl = "https://app.ecwid.com/api/v3/63690252/products"
GifFile = None
ResContent = content = VidFile = seoNameEn = None
count = 0
ProcessedMsgID = False
body = {}

# Creates a product and assign the main product image
async def create_product(message, MCategory, categories, media_path):
    global ResContent, Main, body, seoNameEn

    # Checking message type
    if message:
        try:
            # Text processing
            RefinedTxt = text_processor(message)

            # Condition to check for invalid message length
            if len(RefinedTxt) < 7:
                clearMediaList(files=True)
                logger.error(
                    f"Invalid message length found | Length: {len(RefinedTxt)}"
                )
                return

            # Creating variables with ready to use data from telegram message
            name = RefinedTxt[1].strip()
            nameEn = ts.translate(name)
            nameEn = re.sub('a ', '', nameEn)
            nameEn = nameEn.capitalize()
            # Checking for invalid criteria
            if re.search('السيري', name) or re.search('السيري', name):
                clearMediaList(files=True)
                logger.error(
                    f'Invalid name found ')
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
                clearMediaList(files=True)
                logger.warning(
                    f'Brand found with sku: {sku}')
                return
            main_category = ''
            category_names = set(categories['name'])
            main_category = category_processor(
                telegram_category, main_category, category_names)
            CatName = categories['name']
            CatId = categories['id']

            # Options values
            OpValues = [2, 3, 5]
            OpBody = []

            # Extract options from processed text
            options_fill(RefinedTxt, false, OpValues, OpBody)
            # Assigning categories using a for loop and a condition to match stored category list
            secName, Category, MainCategory, Cats = category_fill(
                main_category, CatName, CatId, MCategory)

            # Create a product request body
            if secName:
                if categories['name']:
                    for catNam in categories['name']:
                        if catNam == secName:
                            seoNameEn = categories['name'].index(catNam)
                            break

                seoNameEn = categories['nameEn'][seoNameEn] + ' / ' + nameEn
                seoName = secName + ' / ' + name
            else:
                seoName = name
                seoNameEn = nameEn
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
                "categoryIds": Category,
                "categories": Cats,
                "defaultCategoryId": MainCategory,
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
                clearMediaList(files=True)
                return None
            elif resCode == 409:
                logger.warning(
                    f"SKU_ALREADY_EXISTS: {sku} | Error Message: {ResContent['errorMessage']} | Error code: {ResContent['errorCode']}"
                )
                await clear_all(media_path)
                return None
            else:
                logger.info(
                    f"Failed to create a new product")
                clearMediaList(files=True)
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
    response = requests.post(eurl, data=postData, headers=headers)
    resCode = int(response.status_code)
    response = json.loads(response.text.encode('utf-8'))
    logger.info("Body request has been sent")
    return response, resCode

# Uploads main image
async def UploadMainIMG(ItemId, Main):
    MainImgData = open(Main, 'rb').read()
    MainImgRes = requests.post(
        f'https://app.ecwid.com/api/v3/63690252/products/{ItemId}/image?token=secret_4i936SRqRp3317MZ51Aa4tVjeUVyGwW7',
        data=MainImgData,
        headers=headers)
    logger.info(
        f'Main image upload is successful | Status code: {MainImgRes.status_code} | Reason: { MainImgRes.reason} | Image name: {Main}'
    )

# Adding gallery images to the product
async def media_check(media_path):
    global GifFile, count
    video_files = []
    VidTypes = ['video/mp4', 'video/avi', 'video/mkv', 'video/mpeg']
    FileTypes = magic.Magic(mime=True)
    for Ip in media_path['image']:
        FileType = FileTypes.from_file(Ip)
        for Vi in VidTypes:
            if Vi == FileType:
                logger.info(
                    f"Video file have been found | File name: {Ip}"
                )
                video_files.append(Ip)
                count += 1
                break
    return video_files

async def vid2Gif(video):
    global GifFile, count
    count += 1
    GifFile = f'media/animpic{str(count)}.gif'
    Vid = VideoFileClip(video).subclip(0, 10).resize(0.5)
    Vid.write_gif(GifFile, program='ffmpeg', fps=24)
    Vid.close()
    size = round(os.path.getsize(GifFile) / 1024**2)
    if size >= 18:
        Vid = VideoFileClip(video).subclip(0, 10).resize(0.5)
        Vid.write_gif(GifFile, program='ffmpeg', fps=15)
        Vid.close()
        size = round(os.path.getsize(GifFile) / 1024**2)
        if size >= 18:
            Vid = VideoFileClip(video).subclip(0, 10).resize(0.5)
            Vid.write_gif(GifFile, program='ffmpeg', fps=10)
            Vid.close()
    logger.info(f"New gif file have been created | File name: {GifFile}")
    return GifFile

async def uploader(ItemId, media_path,  Main):
    global GifFile
    if GifFile:
        GifFile = None
    for img in media_path:
        if img is not None and img != Main:            
            ImgFile = open(img, 'rb')
            r3 = requests.post(
                f'https://app.ecwid.com/api/v3/63690252/products/{ItemId}/gallery?token=secret_4i936SRqRp3317MZ51Aa4tVjeUVyGwW7',
                data=ImgFile,
                headers=headers)
            if r3.ok:
                logger.info(
                f"Gallery image uploaded successfully | Status code: {r3.status_code} | Reason: {r3.reason}"
            )
            else:
                logger.info(
                f"Gallery image has not been uploaded successfully | Status code: {r3.status_code} | Reason: {r3.reason}"
            )

def incoming_message_processor(reqResponse):
    if reqResponse:
        
        
        if reqResponse.message:
            ContentMessage = reqResponse.message
        elif reqResponse.channel_post:
            ContentMessage = reqResponse.channel_post
        elif reqResponse.effective_message:
            ContentMessage = reqResponse.effective_message
        if ContentMessage:
            return ContentMessage

def clearMediaList(*args, clear=bool, files=bool):
    Files = glob.glob('media/*')
    if args:
        dicts = [arg for arg in args]
        for lists in dicts:
            if len(Files) != 0 and clear == True:
                if type(lists) is tuple:
                    for media_list in lists:
                        for media_file in media_list.values():
                            for file in Files:
                                if file == media_file:
                                    os.remove(file)
                        media_list.clear()
                else:
                    for media_file in lists.values():
                        for file in Files:
                            if file == media_file:
                                os.remove(file)
                    media_file.clear()
            elif len(Files) != 0 and files == True:
                for file in Files:
                    os.remove(file)
            elif type(lists) is dict:
                for lis in lists.values():
                    lis.clear()
            else:
                for val in lists:
                    for lis in val.values():
                        lis.clear()
    else:
        if len(Files) != 0 and files == True:
            for file in Files:
                os.remove(file)
    logger.info(
        f"Media list is cleared | Media List: {args} "
    )

def media_download(filePath, fileName):
    # Downloading file and saving to the media folder
    file_name = filePath.download(f'media/{fileName}')
    return file_name

# Downloads media files
def media_downloader(fid, bot):
    """_summary_

        Args:
            media (photo/video): message media file
            bot (client): telegram bot instance

        Returns:
            file_name: Takes message media file and save it locally, then returns new file name as a refrense
        """

    # # # Checking media type
    # bot1 = telegram.Update.de_json(bot1, bot)

    # try:
    # Retrieving file path
    filePath = bot.getFile(fid)
    filePath1 = filePath.file_path

    # Extracting file name
    fileName = re.sub("\w+\W*[^file_\d+.\w]", '', filePath1)

    # Removing extra text
    fileName = fileName.replace('api.telegram.', '')
    file_name = media_download(filePath, fileName)
    logger.info(
        f"Media file download is successful | Status code: 200 | Path: {file_name}"
    )
    # except telegram.error.BadRequest as e:
    #     if re.match('File is too big', e):
    #         logger.warning(
    #             f'File with  ID {fid} contains a big file and will not be downloaded!'
    #         )
    #         return
    # file_name = json.dumps(file_name)
    return file_name

async def clear_all(media_path):
    media_path['image'].clear()
    media_path['grouped_id'].clear()
    Files = glob.glob('media/*')
    for file in Files:
        os.remove(file)
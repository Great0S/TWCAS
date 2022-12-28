# library import
import configparser
import glob
import json
import logging
import os
import re
import sys


def print_log_record_on_error(func):
    def wrap(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except:
            import sys
            print(sys.stderr, 'Unable to create log message msg=%r, args=%r ' % (
                getattr(self, 'msg', '?'), getattr(self, 'args', '?')))
            raise

    return wrap


import requests
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import ChannelParticipantsSearch
from moviepy.editor import VideoFileClip
import magic

# Logging config
logging.LogRecord.getMessage = print_log_record_on_error(logging.LogRecord.getMessage)
logging.basicConfig(
    handlers=[logging.FileHandler(f"logs/{__name__}.log", 'w', 'utf-8'), logging.StreamHandler(sys.stdout)],
    level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

# Read credentials
config = configparser.ConfigParser()
config.read("config.ini")

# Assign values ​​to internal variables
api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
username = config['Telegram']['username']
channel_id = config['Telegram']['channel_id']
token = config['Telegram']['KAtoken']

# create a Telegram client object
client = TelegramClient(username, api_id, api_hash)

client.start(phone=905434050709)

eurl = "https://app.ecwid.com/api/v3/63690252/products"
curl = "https://app.ecwid.com/api/v3/63690252/categories?token=secret_4i936SRqRp3317MZ51Aa4tVjeUVyGwW7"

headers = {
    "Authorization": "Bearer secret_4i936SRqRp3317MZ51Aa4tVjeUVyGwW7",
    "Content-Type": 'application/json;charset: utf-8'
}


async def dump_all_participants(channel):
    """Writes a json file with information about all channel/chat members"""
    offset_user = 0  # member number to start reading from
    limit_user = 100  # maximum number of records transferred at one time

    all_participants = []  # list of all channel members
    filter_user = ChannelParticipantsSearch("")

    while True:
        participants = await client(GetParticipantsRequest(channel, filter_user, offset_user, limit_user, hash=0))
        if not participants.users:
            break
        all_participants.extend(participants.users)
        offset_user += len(participants.users)


async def dump_all_messages(channel):
    """Writes a json file with information about all channel/chat messages"""
    offset_msg = 0  # record number from which reading starts
    limit_msg = 100  # maximum number of records transferred at one time

    all_messages = []  # list of all messages
    total_messages = 0
    total_count_limit = 0  # change this value if you don't need all messages
    Min_ID = int(
        input('Enter 0 for getting all posts or specify the starting post ID: '))

    while True:
        history = await client(GetHistoryRequest(
            peer=channel,
            offset_id=offset_msg,
            offset_date=None, add_offset=0,
            limit=limit_msg, max_id=0, min_id=Min_ID,
            hash=0))
        if not history.messages:
            break
        messages = history.messages
        try:
            for message in messages:
                all_messages.append(message.to_dict())
            offset_msg = messages[len(messages) - 1].id
            total_messages = len(all_messages)
            logging.info(
                f'Records received: {len(all_messages)}')
            if total_count_limit != 0 and total_messages >= total_count_limit:
                break
        except KeyError as e:
            logging.info(f"Messages Key Error: {e}")
            break

    # Creating a Get request for categories
    r1 = requests.get(curl, headers=headers).json()
    pages = int(r1['total'])
    categories = {'id': [], 'name': [], 'parentId': []}

    # Pulling categories data and storing them in a list
    for offset in range(0, pages, 100):
        r2 = requests.get(curl + '&offset=' + str(offset)).json()
        items_list = r2['items']
        for value in items_list:
            try:
                categories['id'].append(value['id'])
                categories['name'].append(value['name'])
                categories['parentId'].append(value['parentId'])
            except KeyError:
                continue

    # List for images path
    Files = []

    # Iterator for looping through all recieved messages from telegram
    for m in all_messages:
        try:
            message = m['message']
            count = 0

            # RegEx for removing special char and spliting text into lines
            RegExForSpecial = re.sub("[🔹💰🌺]", "", message)
            RegExForSpecial = re.sub(" :", "", RegExForSpecial)
            RegExForSpecial = re.sub("[ ]", "", RegExForSpecial)
            RegExForSpecial = re.sub(r'^\s', "", RegExForSpecial)
            RegExForSpecial = re.sub(
                r'^\n|\n\n|\n\n\n|\n\n\n\n|\n\n\n\n\n', "", RegExForSpecial)
            RefinedTxt = RegExForSpecial.splitlines()

            # Condition to check for invalid messages
            if len(RefinedTxt) < 7:
                Files = glob.glob('media\*')
                for file in Files:
                    os.remove(file)
                media_path = []
                logging.error(f"Invalid message length found with message ID:{m['id']}")
                continue

            # Creating variables with ready to use data from telegram message
            name = RefinedTxt[1]
            if re.search('السيري', name) or re.search('السيرى', name):
                Files = glob.glob('media\*')
                for file in Files:
                    os.remove(file)
                media_path = []
                logging.error(f"Invalid name found with message ID: {m['id']}")
                continue
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
            jCategory = RefinedTxt[0]
            if re.search('ماركه', jCategory) or re.search('ماركة', jCategory):
                media_path = []
                logging.warning(f"Brand found with sku: {sku} | Message ID: {m['id']}")
                continue

            jCatName = re.split(r'\W+', jCategory)
            jCatMain = ''
            jCatSec = ''
            jCatSecRev = ''
            ca = set(categories['name'])
            try:
                if re.search(' و ', jCategory):
                    for i in ca:
                        jCatMain = ''
                        if i == jCategory:
                            logging.info(f"Main found with seperator | Category: {i}")
                            jCatMain = jCategory
                            break
                        else:
                            continue

                    if jCatMain != jCategory:
                        jCatMain = ''
                        for jc in range(len(jCatName)):
                            seperator = 'و'
                            if jc < jCatName.index(seperator):
                                jCatMain += ' ' + jCatName[jc]
                                jCatMain = jCatMain.strip()
                                for i in ca:
                                    if i == jCatMain:
                                        logging.info(f"Main found with seperator | Category: {i}")
                                        break
                                else:
                                    continue
                                break
                            else:
                                continue
                        else:
                            logging.warning(f"Main with seperator not found | Message ID: {m['id']}")
                            pass

                    for s in range(len(jCatName)):
                        if s > jCatName.index(seperator):
                            jCatSec += ' ' + jCatName[s]
                            jCatSec = jCatSec.strip()
                            jSecMain = jCatName[0] + ' ' + jCatSec
                            for i in ca:
                                if i == jCatSec:
                                    logging.info(f"Secondry found with seperator 1 | Category: {i}")
                                    break
                                elif i == jSecMain:
                                    jCatSec = jSecMain
                                    logging.info(f"Secondry found with seperator 2 | Category: {i}")
                                    break
                                else:
                                    continue
                            else:
                                continue
                            break
                    else:
                        continue

                elif not re.search(' و ', jCategory):
                    jCatMain = ''
                    for j in range(len(jCatName)):
                        jCatMain += ' ' + jCatName[j]
                        jCatMain = jCatMain.strip()
                        for i in ca:
                            if i == jCatMain:
                                logging.info(f"Main found without seperator | Category: {jCatMain}")
                                break
                        else:
                            continue
                        break
                    pre = jCatMain.split()
                    res = list(set(jCatName).difference(pre))
                    for n in res:
                        jCatSec += ' ' + n
                        jCatSec = jCatSec.strip()
                        if len(jCatSec.split()) > 1:
                            jCatSecRev = jCatSec.split()
                            jCatSecRev = ' '.join(reversed(jCatSecRev))
                        jSecMain = jCatName[0] + ' ' + jCatSec
                        for i in ca:
                            if i == jCatSec:
                                logging.info(f"Secondry found without seperator 1 | Category: {i}")
                                break
                            elif i == jCatSecRev:
                                jCatSec = jCatSecRev
                                logging.info(f"Secondry found without seperator 2 | Category: {i}")
                                break
                            elif i == jSecMain:
                                jCatSec = jSecMain
                                logging.info(f"Secondry found without seperator 3 | Category: {i}")
                                break
                            else:
                                continue
                        else:
                            continue
                        break

                else:
                    logging.warning(
                        f'Main without seperator not found | Message ID: {m["id"]}')
                    continue

            except KeyError as e:
                logging.warning(f"Category processor KeyError occurred: {e}")
                continue
            except IndexError as e:
                logging.warning(f"Category processor ValueError occurred: {e}")
                continue
            CatName = categories['name']
            CatId = categories['id']
            secondCategoryID = None
            defaultCategoryID = None
            secondCategory = None

            # Options values
            OpValues = [2, 3, 5]
            OpBody = []

            # Iterate through all options
            for Op in OpValues:
                Op1Value = ''
                Op = RefinedTxt[Op]
                Op1Name = re.sub('[^ا-ي]', ' ', Op)
                Op1Name = re.sub('^[ \t+]|[ \t]+$', '', Op1Name)

                if not re.match(r'\$|\d{1,3}\.\d{1,3}$', Op) and not re.search(
                        r'(0-9|[a-z]+\.|\s+\b)|(0-9|[A-Z]+\.|\s+\b)', Op) and not re.match(r'\d\w{1,3}\b', Op):
                    Op1ValueD = re.sub('[^$\d]', '', Op)
                    if re.search('\$', Op):
                        Op1ValueD = Op1ValueD.replace('$', "")
                        Op1Value = '$' + Op1ValueD
                    elif int(Op1ValueD) < 100:
                        Op1Value = Op1ValueD
                    else:
                        Op1ValueD = ' - '.join(re.findall('..', Op1ValueD))
                        Op1Value = Op1ValueD
                elif re.match(r'\$|\d{1,3}\.\d{1,3}$', Op) or re.search('\$\d', Op):
                    Op1ValueD = re.sub('[^$\d.]+', '', Op)
                    Op1Value = Op1ValueD
                else:
                    Op1ValueT = re.sub('[^$a-zA-Z\d]', ' ', Op)
                    Op1ValueT = Op1ValueT.strip()
                    Op1ValueT = Op1ValueT.upper()
                    Op1ValueT = re.sub('\s+', ' - ', Op1ValueT)
                    Op1Value = Op1ValueT

                OpBodyValues = {
                                   "type": "RADIO",
                                   "name": Op1Name,
                                   "choices": [
                                       {"text": str(Op1Value), "priceModifier": 0, "priceModifierType": "ABSOLUTE"}],
                                   "defaultChoice": 0,
                                   "required": false
                               },

                OpBody.extend(OpBodyValues)

            # Assigning categories using a for loop and a condition to match stored category list
            for value in CatName:
                if re.match(jCatMain, value) and len(value) == len(jCatMain):
                    secName = value + ' / '
                    defaultCategoryID = CatName.index(value)
                    defaultCategory = CatId[defaultCategoryID]
                    break

                elif re.match(jCatSec, value) and len(value) == len(jCatSec):
                    secondCategoryID = int(CatName.index(value))
                    secondCategory = CatId[secondCategoryID]
                    break

                else:
                    secondCategory = None
                    defaultCategory = None
                    secName = ''
                    Category = []
                    continue

            MainCategory = ''
            secName = secName

            # Validating category data
            try:
                if defaultCategory == MainCategory:
                    Category = [MainCategory, secondCategory]
                    Cats = {"id": MainCategory,
                            "enabled": True}, {"id": secondCategory,
                                               "enabled": True}
                    if secondCategoryID == None:
                        Category = [MainCategory]
                        Cats = {"id": MainCategory,
                                "enabled": True}
                elif defaultCategory != MainCategory:
                    Category = [MainCategory, defaultCategory, secondCategory]
                    Cats = {"id": MainCategory,
                            "enabled": True, "id": defaultCategory}, {
                               "enabled": True, "id": secondCategory}, {
                               "enabled": True}
                    if secondCategoryID == None:
                        Category = [MainCategory, defaultCategory]
                        Cats = {"id": MainCategory,
                                "enabled": True}, {"id": defaultCategory,
                                                   "enabled": True}
                        if defaultCategory == None:
                            Category = [MainCategory]
                            Cats = {"id": MainCategory,
                                    "enabled": True}
            except IndexError:
                defaultCategory = secondCategory
                Category = [MainCategory, defaultCategory]
                Cats = {"id": MainCategory,
                        "enabled": True, "id": defaultCategory,
                        "enabled": True}

            # Create a product request body
            body = {
                "sku": sku,
                "unlimited": true,
                "inStovalue": true,
                "name": name,
                "price": price,
                "enabled": true,
                "options": OpBody,
                "description": "<b>اختار/ي أفضل المنتجات من مئات الماركات الراقية التركية. نقدم لك/ي أكبر تشكيلة    من الملابس التركية واحدث الصيحات في الأزياء النسائية والرجالية والاطفال التي تناسب جميع الأذواق.   بمقاسات وألوان مختلفة.</b>",
                "categoryIds": Category,
                "categories": Cats,
                "defaultCategoryId": MainCategory,
                "seoTitle": f'{secName}{name}',
                "seoDescription": "اختار/ي أفضل المنتجات من مئات الماركات الراقية التركية. نقدم لك/ي أكبر تشكيلة    من الملابس التركية واحدث الصيحات في الأزياء النسائية والرجالية والاطفال التي تناسب جميع الأذواق.   بمقاسات وألوان مختلفة.",
                "attributes": [
                    {"name": "ملاحظة", "value": 'اختيار الألوان يتم عند البدء بتجهيز الطلبية', "show": "DESCR",
                     "type": "BRAND"}],
                "subtitle": "السعر المعروض للسيري كامل"
            }
            count = 0
            msgId = m['id']
            GiD = m['grouped_id']
            MsgDate = m['date']
            media_path = []

            # Parsing collected data into a json
            postData = json.dumps(body)

            # Sending the POST request to create the products
            response = requests.post(
                eurl, data=postData, headers=headers)

            # Checking for response errors
            resError = int(response.status_code)
            if resError == 409:
                Files = glob.glob("media\*")
                for file in Files:
                    os.remove(file)
                media_path = []
                logging.warning(f"SKU_ALREADY_EXISTS: {sku}")
                continue

            # Iterating through the images of every product
            async for massage in client.iter_messages(channel):
                if massage.grouped_id is not None and GiD is not None and massage.id <= msgId:
                    if massage.grouped_id >= GiD and massage.date <= MsgDate:
                        count += 1
                        path = await client.download_media(massage, "media/")
                        logging.info(f"Media file Download Successfull | Status code: 200 | Path: {path}")
                        media_path.append(path)
                        Files.append(path)
                    else:
                        break

                elif GiD is None and massage.grouped_id is None and massage.id <= msgId:
                    if massage.date == MsgDate:
                        count += 1
                        path = await client.download_media(massage, "media/")
                        logging.info(f"Media file Download Successfull | Status code: 200 | Path: {path}")
                        media_path.append(path)
                        Files.append(path)
                    else:
                        break
                else:
                    continue

            # Checking file type and converting video to gif
            ResContent = response.content.decode("utf-8")
            ItemId = re.sub('\D', '', ResContent)
            VidTypes = ['video/mp4', 'video/avi', 'video/mkv', 'video/mpeg']
            FileTypes = magic.Magic(mime=True)
            Temp = []
            count = 0
            for Ip in media_path:
                FileType = FileTypes.from_file(Ip)
                for Vi in VidTypes:
                    if Vi == FileType:
                        GifFile = 'media/animpic' + str(count) + '.gif'
                        Vid = VideoFileClip(Ip).subclip(0, 10).resize(0.5)
                        Vid.write_gif(GifFile, program='ffmpeg', fps=24)
                        Vid.close()
                        size = round(os.path.getsize(GifFile) / 1024 ** 2)
                        if size >= 20:
                            Vid = VideoFileClip(Ip).subclip(0, 10).resize(0.5)
                            Vid.write_gif(GifFile, program='ffmpeg', fps=15)
                            Vid.close()
                        Temp.append(Ip)
                        media_path.append(GifFile)
                        count += 1
                        break
            if len(Temp) != 0:
                for tp in Temp:
                    media_path.remove(tp)

            # Setting product main image
            FileType = FileTypes.from_file(media_path[0])

            MainImgData = open(media_path[0], "rb").read()
            MainImgRes = requests.post(
                f'https://app.ecwid.com/api/v3/63690252/products/{ItemId}/image?token=secret_4i936SRqRp3317MZ51Aa4tVjeUVyGwW7',
                data=MainImgData, headers=headers)
            logging.info(f"Main image status code: {MainImgRes.status_code} | Reason:{MainImgRes.reason}")

            # Adding gallery images to the product
            for img in media_path:
                if img is not media_path[0]:
                    ImgFile = open(img, "rb").read()
                    r3 = requests.post(
                        f'https://app.ecwid.com/api/v3/63690252/products/{ItemId}/gallery?token=secret_4i936SRqRp3317MZ51Aa4tVjeUVyGwW7',
                        data=ImgFile, headers=headers)
                    logging.info(f"Gallery images status code: {r3.status_code} | Reason: {r3.reason}")

            # Response feedback
            logging.info(f"Response: {ResContent} | Status: {response.status_code} | Reason: {response.reason}")

            # Zeroing image names
            media_path = []

        except IndexError as e:
            Files = glob.glob("media\*")
            for file in Files:
                os.remove(file)
            logging.warning(f"Index Error passed: {e} | Message ID: {m['id']}")
            continue

        except KeyError as e:
            Files = glob.glob("media\*")
            for file in Files:
                os.remove(file)
            logging.warning(f"Key Error passed: {e} | Message ID: {m['id']}")
            continue

        except ValueError as e:
            Files = glob.glob("media\*")
            for file in Files:
                os.remove(file)
            logging.warning(f"Value Error passed: {e} | Message ID: {m['id']}")
            continue

    # Removing downloaded files after the loop ends
    media_path = []
    Files = glob.glob("media\*")
    for file in Files:
        os.remove(file)
    logging.info("Product created successfully")


async def main():
    channel = await client.get_entity(url)
    # await dump_all_participants(channel)
    await dump_all_messages(channel)


# clearing the console from unnecessary
def cls(): return os.system("cls")


cls()

# parsing a chat or channel in Telegram and saving to a JSON file
url = 't.me/' + input('Enter the channel name:@')
channel_string = url.split('/')[-1]
logging.info("Parsing started")

with client:
    client.loop.run_until_complete(main())
    logging.info("Parsing finished!")

input("Press Enter to close")

# library import
from __future__ import absolute_import

import json
import logging
import os
import re
from logging import config

import requests
import telegram
from fastapi import Response
from fastapi import Request as FARequest
import uvicorn

from config.logger import Target, bot, chord, fastapi_app, log_config, token
from app.tasks import (DownloadCallback, NewProductCallback, UploadMainIMG,
                       clearMediaList, create_product, dummy, media_check,
                       media_downloader, mediaCallback, uploader, vid2Gif)
from extraction.dump_category import (categories, curl, dump_categories,
                                      eheaders)

config.dictConfig(log_config)
logger = logging.getLogger('mainLog')
payload = {}
headers = {}
requestsList = {'update_id': [], 'post': []}
media_path = {'image': [], 'media_group_id': []}
old_requests = []
count = 0
kadin_ids = [-1001411372097, -1001188747858, -1001147535835, -1001237631051]
messageDate = messageGroupID = responseData = Cmessage = Main = MCategory = category_json = None

def response_body(code, text):
    return Response(f'{text}', code)

def check_request(req):
    global old_requests
    if old_requests:
        if req.json['update_id'] in old_requests:
            return response_body(508, 'Repeated update')
        else:
            old_requests.append(req.json['update_id'])

# Main incoming req processor
@fastapi_app.post("/")
async def index(req):
    global bot, old_requests, media_path, count, messageDate, MCategory, kadin_ids
    global messageGroupID, responseData, Cmessage, Main, categories, reqResponse

    try:
        reqResponse = telegram.Update.de_json(req.json, bot)
        if reqResponse.message:
            processedRequest = reqResponse.message
        elif reqResponse.channel_post:
            processedRequest = reqResponse.channel_post
        elif reqResponse.effective_message:
            processedRequest = reqResponse.effective_message
        if processedRequest:
            if processedRequest.photo or processedRequest.video:
                check_request(req)
                requestsList['update_id'].append(reqResponse.update_id)
                requestsList['post'].append(
                    processedRequest)
                logger.info(
                    f"Processed req with index: {count} has been added")
                count += 1

            if processedRequest.caption:
                check_request(req)
                responseData = None
                if processedRequest.chat_id in kadin_ids:
                    MCategory = 127443592
                elif processedRequest.chat_id == -1001338146588:
                    MCategory = 127443595
                elif processedRequest.chat_id == -1001338084491:
                    MCategory = 127443378
                else:
                    MCategory = None
                    return Response('ok', status=406)

                logger.info(
                    f"Caption found with index {count} | Message update ID: {req.json['update_id']}")
                Cmessage = processedRequest.caption
                messageDate = processedRequest.date
                messageGroupID = processedRequest.media_group_id

        if messageGroupID:
            if any(media_path.values()) == True:
                clearMediaList(media_path, clear=True)
            for c in requestsList['post']:
                if messageGroupID == c.media_group_id:
                    if c.photo:
                        fid = c.photo[len(c.photo) - 1].file_id
                    else:
                        fid = c.video.file_id
                    NewFile = chord(media_downloader.subtask((
                        [fid])))(DownloadCallback.subtask())
                    NewFile.get()
                    if NewFile:
                        media_path['image'].append(
                            NewFile.result[0])
                        media_path['media_group_id'].append(
                            c.media_group_id)
                    else:
                        logger.info(
                            f"Files download is not successful | Message ID: {c.message_id}")
                else:
                    continue

        if Cmessage:

            Main = None
            responseData = chord(create_product.subtask(
                (Cmessage, MCategory, [category_json])))(NewProductCallback.subtask())
            responseData.get()
            if hasattr(responseData, 'result'):
                responseData = responseData.result
            else:
                responseData = None
            Cmessage = processedRequest = messageDate = None

        if responseData:
            if any(media_path['image']):
                media_list = []

                # Media check
                media_path, video_files = media_check(media_path)
                if video_files:
                    for video in video_files:
                        video_processing = chord(vid2Gif.subtask(
                            [video]))(mediaCallback.subtask())
                        video_processing.get()
                        if re.search('mp4', video_processing.result[0]):
                            pass
                        else:
                            media_list.append(
                                video_processing.result[0])

                # Uploads main image
                Main = media_path['image'][0]
                uploadMain = chord(UploadMainIMG.subtask(
                    (responseData, Main, headers)))(dummy.subtask())
                uploadMain.get()

                if messageGroupID == media_path['media_group_id'][0]:

                    # Uploads gallery images
                    uploadMedia = chord(uploader.subtask(
                        (responseData, [media_list], Main)))(mediaCallback.subtask())
                    uploadMedia.get()
                    clearMediaList((media_path), clear=True)
                    logger.info(
                        f'Message update ID: {req.json["update_id"]}')

                    # Response feedback
                    logger.info(
                        f"Files has been uploaded for product: {responseData} | Status: 200 | Reason: ok")
                    return response_body(200, 'ok')
                else:
                    messageGroupID = None
                    return response_body(412, f'Files has not been uploaded for product: {responseData} | Reason: error')

            else:
                logger.info(
                    f"Product created but no media!? | Files: {media_path}")
                return response_body(412, 'Product created but no media!?')

        else:
            return response_body(203, 'Media files ok')

    except telegram.error.BadRequest as e:
        if re.match('File is too big', e):
            logger.warning(
                'Post contains a big file and will not be downloaded!'
            )
            return response_body(412, 'Post contains a big file and will not be downloaded!')
        logger.warning(
            f'Telegram error: {e} | Message ID: {processedRequest.message_id}')
        return response_body(412, f'Telegram error: {e} | Message ID: {processedRequest.message_id}')
    except KeyError as e:
        logger.exception(e)
        pass
    except TypeError as e:
        logger.exception(e)
        pass
    except FileNotFoundError as e:
        logger.warning(
            f"Task script File Not Found Error:  {e} | Message ID: {processedRequest} | Media: {media_path} | List: {requestsList}"
        )
        clearMediaList((media_path, requestsList), files=True)
        return response_body(412, f"Task script File Not Found Error:  {e} | Message ID: {processedRequest} | Media: {media_path} | List: {requestsList}")
    except ValueError as e:
        logger.exception(e)
        return response_body(412, f'Value error: {e}')
    except AttributeError as e:
        logger.exception(e)
        return response_body(412, f'Attribute error: {e}')


# @fastapi_app
# def afterRequest(response):
#     global reqResponse
#     try:
#         global old_requests
#         if req.method == 'POST':
#             if len(old_requests) >= 5000:
#                 old_requests.clear()
#             if hasattr(req, 'json'):
#                 if 'update_id' in req.json:
#                     if len(old_requests) > 3:
#                         check_request(req)
#                         old_requests.append(req.json['update_id'])
#                     else:
#                         old_requests.append(req.json['update_id'])

#         UpdateCount = bot.getWebhookInfo()
#         UpdateCount = UpdateCount['pending_update_count']
#         if UpdateCount == 1:
#             logger.info(f"Updates are finished | Left: {UpdateCount}")
#     except telegram.error.NetworkError as e:
#         logger.exception(f"Main script Network Error: {e}")
#     except Exception as e:
#         logger.exception(e)
#     return response


@fastapi_app.get("/setWebhook/")
def setWebhook():
    url = f"https://api.telegram.org/bot{token}/"

    responseDel = requests.get(url + 'setWebhook?remove=',
                               json=payload, headers=headers)
    responsePost = requests.post(
        url + 'setWebhook?url=' + Target, headers=headers, json=payload)

    if responsePost.status_code == 200:
        logger.info(
            f"Removed old url: {responseDel.status_code} | New webhook has been set successfully! | Status: {responsePost.status_code}"
        )
        return response_body(200, "Webhook has been set successfully")
    else:
        logger.info(
            f'Webhook setting error: {responsePost.status_code} | Webhook error text: {responsePost.text}'
        )
        return response_body(412, "Webhook has not been set successfully")


# @fastapi_app.route("/main", methods=["GET", "POST"])
# def main_page():
#     return render_template("main.html")

# clearing the console from unnecessary


def cls(): return os.system('cls')


cls()


def main():
    global category_json
    File_path = 'extraction/categories.json'
    if os.path.exists(File_path):
        request_category = requests.get(curl, headers=eheaders).json()
        category_total = int(request_category['total'])
        # Dumping categories into a dict var
        open_json = open('extraction/categories.json', encoding='utf-8')
        category_json = json.load(open_json)
        if len(category_json['name']) == category_total:
            pass
        else:
            from threading import Thread
            new_thread = Thread(target=dump_categories)
            new_thread.start()
            new_thread.join()
            with open(File_path, 'w', encoding='utf-8') as file:
                json.dump(categories, file, ensure_ascii=False)
            file.close()
            category_json = categories

    else:
        from threading import Thread
        new_thread = Thread(target=dump_categories)
        new_thread.start()
        new_thread.join()
        with open(File_path, 'w', encoding='utf-8') as file:
            json.dump(categories, file, ensure_ascii=False)
        file.close()
        category_json = categories

    logger.info('Bot started')


# parsing a chat or channel in Telegram and saving to a JSON file
logger.info('Server started')

if __name__ == '__main__':
    main()
    fastapi_app.debug = True
    # fastapi_app.run()
    uvicorn.run(fastapi_app, host="127.0.0.1", port=8000)

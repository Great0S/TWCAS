# library import
from __future__ import absolute_import

import os
import re

import requests
from flask import Response, render_template, request

from app.celery_server import chord, flask_app
from app.tele_bot import bot as client
from config.settings import settings
from models.dump_category import categories, check_category
from tasks.callbacks import NewProductCallback, dummy, mediaCallback
from tasks.checks import clear_all, media_check, vid2Gif
from tasks.create_products import create_product
from tasks.uploader import gallery_uploader, upload_main_image

logger = settings.logger

requestsList = {'update_id': [], 'post': []}
media_path = {'image': [], 'media_group_id': []}
media_files = old_requests = []
count = 0
kadin_ids = settings.women_ids
messageDate = messageGroupID = responseData = Cmessage = Main = MCategory = category_json = None

def response_body(code, text):
    return Response(f'{text}', code)

def check_request(request):
    global old_requests
    if old_requests:
        if request.json['update_id'] in old_requests:
            return response_body(508, 'Repeated update')
        else:
            old_requests.append(request.json['update_id'])

# Main incoming request processor
@flask_app.route("/", methods=["POST", "GET"])
def index():
    global bot, old_requests, media_path, count, messageDate, MCategory, kadin_ids
    global messageGroupID, responseData, Cmessage, Main, categories, reqResponse

    try:
        channel = request.message.input_chat
        
        if reqResponse.message:
            processedRequest = reqResponse.message
        elif reqResponse.channel_post:
            processedRequest = reqResponse.channel_post
        elif reqResponse.effective_message:
            processedRequest = reqResponse.effective_message
        if processedRequest:
            if processedRequest.photo or processedRequest.video:
                check_request(request)
                requestsList['update_id'].append(reqResponse.update_id)
                requestsList['post'].append(
                    processedRequest)
                logger.info(
                    f"Processed request with index: {count} has been added")
                count += 1

            if processedRequest.caption:
                check_request(request)
                responseData = None
                if processedRequest.chat_id in kadin_ids:
                    MCategory = 127443592
                else:
                    MCategory = None
                    return Response('ok', status=406)

                logger.info(
                    f"Caption found with index {count} | Message update ID: {request.json['update_id']}")
                Cmessage = processedRequest.caption
                messageDate = processedRequest.date
                messageGroupID = processedRequest.media_group_id
                media_files.sort()

        if messageGroupID:
                clear_all(media_path)
                download_media_files(channel)

        if Cmessage:
            Main = None
            responseData = chord(create_product.subtask(
                (Cmessage, MCategory, [category_json], [media_path])))(NewProductCallback.subtask())
            responseData.get()
            if hasattr(responseData, 'result'):
                responseData = responseData.result
            else:
                responseData = None
            Cmessage = processedRequest = messageDate = None

        if responseData:
            if any(media_path['image']):

                # Media check
                video_files = media_check(media_path)
                if video_files:
                    for video in video_files:
                        video_processing = chord(vid2Gif.subtask(
                            [video]))(mediaCallback.subtask())
                        video_processing.get()
                        media_path['image'].append(
                                    video_processing.result[0])
                        if re.search('.mp4', video):
                                media_path['image'].remove(video)

                # Uploads main image
                Main = media_path['image'][0]
                uploadMain = chord(upload_main_image.subtask(
                    (responseData, Main)))(dummy.subtask())
                uploadMain.get()

                if messageGroupID == media_path['media_group_id'][0]:

                    # Uploads gallery images
                    uploadMedia = chord(gallery_uploader.subtask(
                        (responseData, [media_path['image']], Main)))(mediaCallback.subtask())
                    uploadMedia.get()
                    clear_all(media_path)
                    return response_body(200, 'ok')
                else:
                    clear_all(media_path)                    
                    messageGroupID = None
                    return response_body(412, f'Files has not been uploaded for product: {responseData} | Reason: error')

            else:
                logger.info(
                    f"Product created but no media!? | Files: {media_path}")
                return response_body(412, 'Product created but no media!?')

        else:
            return response_body(203, 'Media files ok')

    # except telegram.error.BadRequest as e:
    #     if re.match('File is too big', e):
    #         logger.warning(
    #             'Post contains a big file and will not be downloaded!'
    #         )
    #         return response_body(412, 'Post contains a big file and will not be downloaded!')
    #     logger.warning(
    #         f'Telegram error: {e} | Message ID: {processedRequest.message_id}')
    #     return response_body(412, f'Telegram error: {e} | Message ID: {processedRequest.message_id}')
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
        clear_all(media_path)
        return response_body(412, f"Task script File Not Found Error:  {e} | Message ID: {processedRequest} | Media: {media_path} | List: {requestsList}")
    except ValueError as e:
        logger.exception(e)
        return response_body(412, f'Value error: {e}')
    except AttributeError as e:
        logger.exception(e)
        return response_body(412, f'Attribute error: {e}')


# @flask_app
# def afterRequest(response):
#     global reqResponse
#     try:
#         global old_requests
#         if request.method == 'POST':
#             if len(old_requests) >= 5000:
#                 old_requests.clear()
#             if hasattr(request, 'json'):
#                 if 'update_id' in request.json:
#                     if len(old_requests) > 3:
#                         check_request(request)
#                         old_requests.append(request.json['update_id'])
#                     else:
#                         old_requests.append(request.json['update_id'])

#         UpdateCount = bot.getWebhookInfo()
#         UpdateCount = UpdateCount['pending_update_count']
#         if UpdateCount == 1:
#             logger.info(f"Updates are finished | Left: {UpdateCount}")
#     except telegram.error.NetworkError as e:
#         logger.exception(f"Main script Network Error: {e}")
#     except Exception as e:
#         logger.exception(e)
#     return response


@flask_app.route("/setWebhook/")
def setWebhook():
    token = settings.token
    url = f"https://api.telegram.org/bot{token}/"

    responseDel = requests.get(url + 'setWebhook?remove=',
                               json=settings.payload, headers=settings.ecwid_headers)
    responsePost = requests.post(
        url + 'setWebhook?url=' + settings.Target, headers=settings.ecwid_headers, json=settings.payload)

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


@flask_app.route("/main", methods=["GET"])
def main_page():
    return render_template("main.html")



async def download_media_files(channel):
    count = 0
    async for entity in client.iter_messages(entity=channel, wait_time=0, min_id=media_files[0], max_id=media_files[len(media_files)-1]+1):
        if messageGroupID == entity.grouped_id:
            count += 1
            file = ''
            if entity.photo:
                file = f'photo{count}.jpg'
            else:
                file = f'video{count}.mp4'

            NewFile = client.download_media(entity, f"media/{file}")
            if NewFile:
                media_path['image'].append(
                                NewFile)
                media_path['grouped_id'].append(
                                entity.grouped_id)
            else:
                logger.error(
                                f"Files download is not successful | Message ID: {entity.id}")
        else:
            continue





# clearing the console from unnecessary
def cls(): return os.system('cls')


cls()


def main():
    global category_json
    check_category()

    logger.info('Bot started')


# parsing a chat or channel in Telegram and saving to a JSON file
logger.info('Server started')

if __name__ == '__main__':
    flask_app.debug = True
    flask_app.run()

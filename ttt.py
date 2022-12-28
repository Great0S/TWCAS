# library import
from __future__ import absolute_import
import os
import re
import requests
import telegram
import logging
from logging import config
from flask import Response, render_template, request

from app.celery_server import Config, Target, flask_app, chord, log_config, bot, token
from app.tasks import UploadMainIMG, create_product, DownloadCallback, dummy, media_downloader, clearMediaList, upload_media, NewProductCallback

global old_requests

config.dictConfig(log_config)
logger = logging.getLogger('mainLog')
payload = {}
headers = {}
requestsList = {'update_id': [], 'post': []}
media_path = {'image': [], 'media_group_id': []}
MCategory = int(Config['Telegram']['KAcategory'])
old_requests = []
RequestCheck = False
count = 0
response = messageDate = messageGroupID = responseData = ProcessedMsgID = Cmessage = Main = None


# Main incoming request processor
@flask_app.route("/", methods=["POST", "GET"])
def index():
    global bot, old_requests, media_path, count, response, messageDate, messageGroupID, responseData, ProcessedMsgID, Cmessage, Main
    global old_requests

    if old_requests:
        for oReq in old_requests:
            if int(oReq) == request.json['update_id']:
                return Response('Repeated update', status=508)
    try:
        reqResponse = telegram.Update.de_json(request.json, bot)
        if reqResponse.message:
            processedRequest = reqResponse.message
        elif reqResponse.channel_post:
            processedRequest = reqResponse.channel_post
        elif reqResponse.effective_message:
            processedRequest = reqResponse.effective_message
        if processedRequest:
            if processedRequest.photo or processedRequest.video:
                requestsList['update_id'].append(reqResponse.update_id)
                requestsList['post'].append(
                    processedRequest)
                logger.info(
                    f"Processed request with index: {count} has been added")
                count += 1

            if processedRequest.caption:
                ProcessedMsgID = False
                response = None
                logger.info(f"Caption found")
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
            if ProcessedMsgID is False:
                Main = None
                responseData = chord(create_product.subtask(
                    (Cmessage, MCategory)))(NewProductCallback.subtask())
                responseData.get()
                if hasattr(responseData, 'result'):
                    responseData = responseData.result
                else:
                    responseData = None
                ProcessedMsgID = True
                Cmessage = processedRequest = messageDate = None
            else:
                ProcessedMsgID = False
        if responseData:
            response = responseData
            # Uploads main image
            if any(media_path['image']):
                Main = media_path['image'][0]
            else:
                logger.info(
                    f"Product created but no media!? | Files: {media_path}")
                return
            uploadMain = chord(UploadMainIMG.subtask(
                (response, Main, headers)))(dummy.subtask())
            uploadMain.get()
            logger.info(
                f'Message update ID: {request.json["update_id"]}')
            responseData = None

        if response is not None and any(media_path.values()) == True:
            if messageGroupID == media_path['media_group_id'][0]:

                # Uploads gallery images
                uploadMedia = chord(upload_media.subtask(
                    (response, [media_path], Main)))(dummy.subtask())
                uploadMedia.get()
                clearMediaList((media_path, requestsList), clear=True)

                # Response feedback
                logger.info(
                    f"Files has been uploaded for product: {response} | Status: 200 | Reason: ok")
            else:
                ProcessedMsgID = False
                response = None
                messageGroupID = None

    except telegram.error.BadRequest as e:
        if re.match('File is too big', e):
            logger.warning(
                'Post contains a big file and will not be downloaded!'
            )
            return
        logger.warning(
            f'Telegram error: {e} | Message ID: {processedRequest.message_id}')
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
        return
    except ValueError as e:
        logger.exception(e)
        return
    except AttributeError as e:
        logger.exception(e)
        return

    return Response('ok', status=200)


@flask_app.after_request
def afterRequest(response):
    try:
        global old_requests
        if request.method == 'POST':
            if len(old_requests) >= 7000:
                old_requests.clear()
            if hasattr(request, 'json'):
                if 'update_id' in request.json:
                    if len(old_requests) > 3:
                        for oReq in old_requests:
                            if int(oReq) == request.json['update_id']:
                                break
                            else:
                                old_requests.append(request.json['update_id'])
                                break
                    else:
                        old_requests.append(request.json['update_id'])

        UpdateCount = bot.getWebhookInfo()
        UpdateCount = UpdateCount['pending_update_count']
        if UpdateCount == 1:
            logger.info("Updates are finished")
    except telegram.error.NetworkError as e:
        logger.warning(f"Main script Network Error: {e}")
    except Exception as e:
        logger.exception(e)
    return response


@flask_app.route("/setWebhook/")
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
        return "Webhook has been set successfully"
    else:
        logger.info(
            f'Webhook setting error: {responsePost.status_code} | Webhook error text: {responsePost.text}'
        )
        return "Webhook has not been set successfully"


@flask_app.route("/main", methods=["GET", "POST"])
def main_page():
    return render_template("main.html")

# clearing the console from unnecessary
def cls(): return os.system('cls')


cls()


def main():
    logger.info('Bot started')


# parsing a chat or channel in Telegram and saving to a JSON file
logger.info('Server started')

if __name__ == '__main__':
    flask_app.debug = True
    flask_app.run()


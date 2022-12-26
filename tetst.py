from logging import config
import logging
import os
import re
import time

from telethon import events, errors
from config.settings import settings
from config.logger import log_config
from app.tele_bot import bot as client
from app.tasks import clear_all, create_product, incoming_message_processor, media_check, vid2Gif, uploader, UploadMainIMG
from extraction.dump_category import check_category

config.dictConfig(log_config)
logger = logging.getLogger('mainLog')
payload = {}
media_files = old_requests = []
media_path = {'image': [], 'grouped_id': []}
count = 0
kadin_ids = settings.women_ids
client.start(phone=settings.phone)
client.flood_sleep_threshold = 0


@client.on(events.NewMessage(chats=kadin_ids))
async def handler(event):
    global old_requests, media_path, count, messageDate, MCategory, kadin_ids, url
    global messageGroupID, responseData, Cmessage, Main, categories, reqResponse
    try:
        channel = event.message.input_chat
        request = incoming_message_processor(event)
        if request.photo or request.video:
            media_files.append(event.id)
            logger.info(
                f"Media request with index {count} has been added")
            count += 1

        if request.message:
            logger.info(
                f"Text request with index {count} has been added")
            responseData = None
            # if request.chat_id in kadin_ids:
            MCategory = 127443592
            # else:
            #     MCategory = 0
            #     return logger.warning(f"Category unknown | Message: {request.message.id}")

            Cmessage = request.message
            messageDate = request.date
            messageGroupID = request.grouped_id
            media_files.sort()
            client.receive_updates = False

            if messageGroupID:
                await clear_all(media_path)
                await download_media_files(channel)

            if Cmessage:
                Main = None
                responseData = await create_product(
                    Cmessage, MCategory, categories, media_path)
                Cmessage = messageDate = None

            if responseData:
                if any(media_path['image']):

                    # Media check
                    video_files = await media_check(media_path)
                    if video_files:
                        for video in video_files:
                            video_processing = await vid2Gif(video)
                            media_path['image'].append(
                                    video_processing)
                            if re.search('.mp4', video):
                                media_path['image'].remove(video)
                                

                    # Uploads main image
                    Main = media_path['image'][0]
                    await UploadMainIMG(responseData, Main)

                    if messageGroupID == media_path['grouped_id'][0]:
                        # Uploads gallery images
                        await uploader(responseData, media_path['image'], Main)
                        await clear_all(media_path)
                    else:
                        messageGroupID = None
                        logger.error(
                            f'Files has not been uploaded for product: {responseData} | Message ID: {event.id} | Reason: media group id mismatch | Message group id: {messageGroupID} | Media group id: {media_path["grouped_id"][0]}')
                        await clear_all(media_path)
                        client.receive_updates = True


                else:
                    logger.info(
                        f"Product created, but no media!? | Message ID: {event.id} | Files: {media_path}")

    except errors.FloodWaitError as e:
        logger.error('Flood wait for ', e.seconds)
        time.sleep(e.seconds)
    except errors.rpcerrorlist.AuthKeyDuplicatedError as e:
        logger.error(e)

async def download_media_files(channel):
    count = 0
    async for entity in client.iter_messages(entity=channel, wait_time=1, min_id=media_files[0], max_id=media_files[len(media_files)-1]+1):
        if messageGroupID == entity.grouped_id:
            count += 1
            file = ''
            if entity.photo:
                file = f'photo{count}.jpg'
            else:
                file = f'video{count}.mp4'

            NewFile = await client.download_media(entity, f"media/{file}")
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



def cls(): return os.system('cls')


cls()

logger.info("Scraper started")


async def main():
    global categories
    categories = check_category()
    
    async with client:
        await client.run_until_disconnected()

client.loop.run_until_complete(main())
logger.info("Scraping finished!")

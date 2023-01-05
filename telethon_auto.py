import glob
import logging
import os
import re
import time
from logging import config

from telethon import errors, events

from app.tele_bot import bot as client
from config.logger import log_config
from config.settings import settings
from models.dump_category import check_category
from tasks.checks import (incoming_message_check, media_check,
                          vid2Gif)
from tasks.create_products import create_product
from tasks.uploader import gallery_uploader, upload_main_image

config.dictConfig(log_config)
logger = logging.getLogger('mainLog')
payload = {}
media_files = old_requests = []
media_path = {'image': [], 'grouped_id': []}
count = 0
kadin_ids = settings.women_ids
client.start(phone=settings.phone)
client.flood_sleep_threshold = 0


def clear_all(media_path):
    media_path['image'].clear()
    media_path['grouped_id'].clear()
    Files = glob.glob('media/*')
    for file in Files:
        os.remove(file)
        

@client.on(events.NewMessage(chats=kadin_ids))
async def handler(event):
    global old_requests, media_path, count, messageDate, MCategory, kadin_ids, url
    global messageGroupID, responseData, Cmessage, Main, categories, reqResponse
    try:
        if os.path.exists('women_tele_bot.session'):
            channel = client.session.get_input_entity(event.message.chat_id)
        else:
            channel = await client.get_entity(event.message.chat_id)
        request = incoming_message_check(event)
        if request.photo or request.video:
            media_files.append(event.id)
            logger.info(
                f"Media request with index {count} has been added")
            count += 1

        if request.message:
            logger.info(
                f"Text request with index {count} has been added")
            responseData = None
            MCategory = 127443592

            Cmessage = request.message
            messageDate = request.date
            messageGroupID = request.grouped_id
            media_files.sort()
            client.receive_updates = False

            if messageGroupID:
                clear_all(media_path)
                await download_media_files(channel)
                media_files.clear()
            elif not messageGroupID and len(media_files) <= 2:
                clear_all(media_path)
                await download_media_files(channel)
                media_files.clear()
            else:
                logger.error(f"No media group id found | Media files length: {len(media_files)} | Text: {Cmessage}")
                media_files.clear()
                
            if Cmessage:
                Main = None
                responseData = create_product(
                    Cmessage, MCategory, categories, media_path)
                Cmessage = messageDate = None

            if responseData:
                if any(media_path['image']):

                    # Media check
                    video_files = media_check(media_path)
                    if video_files:
                        for video in video_files:
                            video_processing = vid2Gif(video)
                            media_path['image'].append(
                                    video_processing)
                            if re.search('.mp4', video):
                                media_path['image'].remove(video)
                                

                    # Uploads main image
                    Main = media_path['image'][0]
                    upload_main_image(responseData, Main)
                    del media_path['image'][0]

                    for group_id in media_path['grouped_id']:
                        if messageGroupID == group_id:
                            
                            # Uploads gallery images
                            gallery_uploader(
                                responseData, media_path['image'])
                            clear_all(media_path)
                            client.receive_updates = True
                            break
                        else:
                            del media_path['grouped_id'][media_path['grouped_id'].index(group_id)]
                            del media_path['image'][media_path['grouped_id'].index(group_id)]                          
                            continue


                else:
                    logger.info(
                        f"Product created, but no media!? | Message ID: {event.id} | Files: {media_path}")

    except errors.FloodWaitError as e:
        logger.error('Flood wait for ', e.seconds)
        time.sleep(e.seconds)
    except errors.rpcerrorlist.AuthKeyDuplicatedError as e:
        logger.error(e)
    except ValueError as e:
        if re.findall('Could not find input entity with key', e.args[0]):
            channel = await client.get_input_entity(event.message.chat_id)

async def download_media_files(channel):
    count = 0
    async for entity in client.iter_messages(entity=channel, wait_time=1, ids=media_files): #max_id=media_files[len(media_files)-1]+1):
            count += 1
            file = None
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
                logger.error(f"Files download is not successful | Message ID: {entity.id}")
    



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
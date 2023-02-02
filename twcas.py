import glob
import os
import re
import time

from telethon import errors, events

from app.tele_bot import bot as client
from app.tele_bot import alert_bot as alert
from config.settings import settings
from models.dump_category import check_category
from tasks.checks import (clear_all, incoming_message_check, media_check,
                          vid2Gif)
from tasks.create_products import create_product
from tasks.erros_notify import feedback
from tasks.uploader import gallery_uploader, upload_main_image

logger = settings.logger
payload = {}
media_files = []
media_path = {'image': [], 'grouped_id': []}
count = 0
chat = settings.women_ids
client.start(phone=settings.phone)
alert.start(bot_token=settings.alert_bot_token)
client.flood_sleep_threshold = 0
product_response = None


@client.on(events.NewMessage(chats=chat))
async def handler(event):
    global sku, media_path, count, messageDate, main_category_id, url
    global messageGroupID, product_response, caption_message, main_image_name, categories, reqResponse
    try:
        if os.path.exists(f'{settings.session_name}.session'):
            channel = client.session.get_input_entity(event.message.chat_id)
        else:
            channel = await client.get_entity(event.message.chat_id)
        request = await incoming_message_check(event)
        if request.photo or request.video:
            media_files.append(event.id)
            logger.info(
                f"Media request with index {count} has been added")
            count += 1

        if request.message:
            logger.info(
                f"Text request with index {count} has been added")
            product_response = None
            main_category_id = settings.category_id

            caption_message = request.message
            messageDate = request.date
            messageGroupID = request.grouped_id
            media_files.sort()
            client.receive_updates = False

            if caption_message:
                main_image_name = None
                product_response, sku = await create_product(caption_message, main_category_id, categories, media_path, alert)
                caption_message = messageDate = None

        if product_response:
            if messageGroupID:
                await clear_all(media_path)
                await download_media_files(channel, messageGroupID, sku)
                media_files.clear()
            elif not messageGroupID and len(media_files) <= 2:
                await clear_all(media_path)
                await download_media_files(channel, messageGroupID, sku)
                media_files.clear()
            else:
                await feedback(settings.session_name, f"No media group id found | Text: {caption_message} | Sku: {sku}", 'error', alert)
                media_files.clear()

            if any(media_path['image']):
                if messageGroupID == media_path['grouped_id'][0]:
                    # Media check
                    video_files = media_check(media_path)
                    if video_files:
                        for video in video_files:
                            video_processing = await vid2Gif(video)
                            media_path['image'].append(
                                video_processing)
                            if re.search('.mp4', video):
                                media_path['image'].remove(video)

                        # Uploads main_image_name image
                        main_image_name = media_path['image'][0]
                        await upload_main_image(product_response, main_image_name, alert)
                        del media_path['image'][0]
                    else:
                        await feedback(settings.session_name, f"Product created, but no media!? | Message ID: {event.id} | Files: {media_files} | Sku: {sku}", 'error', alert)
                        return

                    # Uploads gallery images
                    for group_id in media_path['grouped_id']:
                        if messageGroupID == group_id:
                            # Uploads gallery images
                            await gallery_uploader(
                                product_response, media_path['image'], alert)
                            await clear_all(media_path)
                            client.receive_updates = True
                            break
                        else:
                            del media_path['grouped_id'][media_path['grouped_id'].index(
                                group_id)]
                            del media_path['image'][media_path['grouped_id'].index(
                                group_id)]
                            continue
            else:
                pass

    except errors.FloodWaitError as e:
        logger.warning('Flood wait for ', e.seconds)
        time.sleep(e.seconds)
    except errors.rpcerrorlist.AuthKeyDuplicatedError as e:
        logger.error(e)
    except ValueError as e:
        if re.findall('Could not find input entity with key', e.args[0]):
            channel = await client.get_input_entity(event.message.chat_id)
        else:
            await feedback(settings.session_name, f"Value error: {e} | Message ID: {event.message.id}", 'error', alert)
    except TypeError as e:
        await feedback(settings.session_name, f"Type error: {e} | Message ID: {event.message.id}", 'error', alert)


async def download_media_files(channel, group_id, sku):
    count = 0
    async for entity in client.iter_messages(entity=channel, wait_time=1, ids=media_files):
        if entity:
            if entity.grouped_id == group_id:
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
                    await feedback(settings.session_name, f"Files download is not successful | Message ID: {entity} | Sku: {sku}", 'error', alert)
            else:
                continue
        else:
            await feedback(settings.session_name, f"Media message is empty | Sku: {sku}", 'error', alert)


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

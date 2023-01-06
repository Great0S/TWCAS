import requests
from config.settings import settings
from tasks.erros_notify import feedback


logger = settings.logger

# Uploads main image
async def upload_main_image(ItemId, Main, alert):
    main_image_data = open(Main, 'rb').read()
    main_image_response = requests.post(
        f'https://app.ecwid.com/api/v3/63690252/products/{ItemId}/image?token=secret_4i936SRqRp3317MZ51Aa4tVjeUVyGwW7',
        data=main_image_data,
        headers=settings.ecwid_headers)
    if main_image_response.status_code == 200:
        logger.info(f'Main image uploaded successfully: {Main}')
    else:
        await feedback(settings.session_name, f"Main image upload failed: {Main} | Product: {ItemId}", 'error', alert)

# Adding gallery images to the product
async def gallery_uploader(ItemId, media_path, alert):

    for img in media_path:
        if img:
            ImgFile = open(img, 'rb')
            gallery_response = requests.post(
                f'https://app.ecwid.com/api/v3/63690252/products/{ItemId}/gallery?token=secret_4i936SRqRp3317MZ51Aa4tVjeUVyGwW7',
                data=ImgFile,
                headers=settings.ecwid_headers)
            if gallery_response.status_code == 200:
                logger.info(f'Gallery image uploaded successfully: {img}')
            else:
                await feedback(settings.session_name, f'Gallery image upload failed: {img} | Error: {gallery_response.content}', 'error', alert)             
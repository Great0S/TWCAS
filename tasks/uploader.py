import requests
from config.settings import settings
from app.celery_server import celery


logger = settings.logger

# Uploads main image
@celery.task()
def upload_main_image(ItemId, Main):
    main_image_data = open(Main, 'rb').read()
    main_image_response = requests.post(
        f'https://app.ecwid.com/api/v3/63690252/products/{ItemId}/image?token=secret_4i936SRqRp3317MZ51Aa4tVjeUVyGwW7',
        data=main_image_data,
        headers=settings.ecwid_headers)
    logger.info(
        f'Main image upload is successful | Status code: {main_image_response.status_code} | Reason: { main_image_response.reason} | Image name: {Main}'
    )

# Adding gallery images to the product
@celery.task()
def gallery_uploader(ItemId, media_path,  Main):
    
    for img in media_path:
        if img is not None and img != Main:            
            ImgFile = open(img, 'rb')
            r3 = requests.post(
                f'https://app.ecwid.com/api/v3/63690252/products/{ItemId}/gallery?token=secret_4i936SRqRp3317MZ51Aa4tVjeUVyGwW7',
                data=ImgFile,
                headers=settings.ecwid_headers)
            if r3.ok:
                logger.info(
                f"Gallery image uploaded successfully | Status code: {r3.status_code} | Reason: {r3.reason}"
            )
            else:
                logger.info(
                f"Gallery image has not been uploaded successfully | Status code: {r3.status_code} | Reason: {r3.reason}"
            )

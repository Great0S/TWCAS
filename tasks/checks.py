import glob
import os
import magic

from moviepy.editor import VideoFileClip
from config.settings import settings

logger = settings.logger
count = 0

def media_check(media_path):
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


def vid2Gif(video):
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

def clear_all(media_path):
    media_path['image'].clear()
    media_path['grouped_id'].clear()
    Files = glob.glob('media/*')
    for file in Files:
        os.remove(file)
        
def incoming_message_check(reqResponse):
    if reqResponse:        
        if reqResponse.message:
            ContentMessage = reqResponse.message
        elif reqResponse.channel_post:
            ContentMessage = reqResponse.channel_post
        elif reqResponse.effective_message:
            ContentMessage = reqResponse.effective_message
        if ContentMessage:
            return ContentMessage
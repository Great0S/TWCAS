import re

from config.settings import settings

logger = settings.logger

# RegEx for removing special char and spliting text into lines
def text_processor(message):
    RegExForSpecial = re.sub("[🔹💰🌺]", "", message)
    RegExForSpecial = re.sub(" :", "", RegExForSpecial)
    RegExForSpecial = re.sub("[ ]", "", RegExForSpecial)
    RegExForSpecial = re.sub(r'^\s', "", RegExForSpecial)
    RegExForSpecial = re.sub(
        r'^\n|\n\n|\n\n\n|\n\n\n\n|\n\n\n\n\n', "", RegExForSpecial)
    RefinedTxt = RegExForSpecial.splitlines()
    logger.info("Text has been processed")
    return RefinedTxt

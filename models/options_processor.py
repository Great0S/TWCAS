import re

from config.settings import settings

logger = settings.logger

# Extract options from processed text
def options_fill(RefinedTxt, false, OpValues, OpBody):

    for Op in OpValues:
        Op1Value = ''
        Op = RefinedTxt[Op]
        Op1Name = re.sub('[^ا-ي]', ' ', Op)
        Op1Name = re.sub('^[ \t+]|[ \t]+$', '', Op1Name)

        if re.search('\$', Op):
            Op = re.sub('[^\da-zA-Z$.]', '', Op)
            Op1Value = Op
        else:
            Op1ValueT = re.sub('[^$a-zA-Z\d]', ' ', Op)
            Op1ValueT = Op1ValueT.strip()
            Op1ValueT = Op1ValueT.upper()
            Op1ValueT = re.sub('\s+', ' - ', Op1ValueT)
            Op1Value = Op1ValueT
        Op1NameEn = ''
        if Op1Name:
            if re.search('سنة', Op1Name):
                Op1Name = 'الفئة العمرية'
                Op1NameEn = 'Age range'
            elif re.search('مقاسات', Op1Name):
                Op1NameEn = 'Set sizes'
            elif re.search('عدد القطع', Op1Name):
                Op1NameEn = 'Pieces in a set'
            elif re.search('سعر', Op1Name):
                Op1NameEn = 'Price per piece'

        OpBodyValues = {
            "type": "RADIO",
                    "name": Op1NameEn,
                    "nameTranslated":  {
                        "ar": Op1Name,
                        "en": Op1NameEn
                    },
            "choices": [{"text": str(Op1Value), "priceModifier": 0, "priceModifierType": "ABSOLUTE"}],
            "defaultChoice": 0,
            "required": false
        },

        OpBody.extend(OpBodyValues)
    logger.info("Options have been populated")

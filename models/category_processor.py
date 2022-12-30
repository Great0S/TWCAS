from config.settings import settings

logger = settings.logger

def category_processor(telegram_category, main_category, categories):
    main_category_en = None
    try:
        for value in categories:
            for item in value:
                if item['nameTranslated']['ar'] == telegram_category:
                    main_category = telegram_category
                    main_category_en = item['name']
                    break
                else:
                    main_category = None
        if main_category:
            logger.info(
                f"Category processed successfully | Arabic: {main_category}")
        else:
            logger.warning(
                f"Category {telegram_category} is not on the list")

    except KeyError as e:
        logger.warning(f'Category processor KeyError occurred: {e}')
        pass
    except IndexError as e:
        logger.warning(f'Category processor ValueError occurred: {e}')
        pass
    return main_category, main_category_en

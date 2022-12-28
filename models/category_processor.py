from config.settings import settings

logger = settings.logger

def category_processor(telegram_category, main_category, category_names):
    try:
        for name in category_names:
            if name == telegram_category:
                main_category = telegram_category
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
    return main_category

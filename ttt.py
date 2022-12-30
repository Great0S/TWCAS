from config.settings import settings
from models.dump_category import check_category
logger = settings.logger

categors = check_category()
main_category = 'جاكيتات ومعاطف'
MCategory = 127443592

def category_fill(main_category, categors, MCategory):
    global default_category_name
    default_category_ID = None
    default_category_name = None
    for value in categors:
        for item in value:
            if item['nameTranslated']['ar'] == main_category:
                default_category_name = item['nameTranslated']['ar']
                default_category_ID = item['id']
                break
            elif item['nameTranslated']['ar'] == main_category:
                if item['parentId'] == MCategory:
                    default_category_name = main_category
                    default_category_ID = item['id']
            else:
                default_category_ID = None
                default_category_name = None
                categories_ids = []
                continue

    main_category_id = int(MCategory)

    # Validating categories_ids data
    try:
        if default_category_ID == main_category_id:
            categories_ids = [main_category_id]
            categories_json = {"id": main_category_id,
                               "enabled": True}
        elif not default_category_ID:
            categories_ids = [main_category_id]
            categories_json = {"id": main_category_id,
                               "enabled": True}
        else:
            categories_ids = [main_category_id, default_category_ID]
            categories_json = {"id": main_category_id,
                               "enabled": True}, {"id": default_category_ID,
                                                  "enabled": True}

    except Exception as e:
        logger.exception(f"Category filling error occurred: {e}")
        default_category_ID = main_category_id
        categories_ids = [main_category_id]
        # noinspection PyDictDuplicateKeys
        categories_json = {"id": main_category_id,
                           "enabled": True}
    logger.info("Category filling is done")
    return default_category_name, categories_ids, main_category_id, categories_json

category_fill(main_category, categors, MCategory)
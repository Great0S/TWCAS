from config.settings import settings

logger = settings.logger

def category_fill(main_category, category_names, category_ids, MCategory):
    global category_name
    defaultCategoryID = None
    defaultCategory = None
    category_name = None
    for value in category_names:
        if value == main_category and len(value) == len(main_category):
            category_name = value
            defaultCategoryID = category_names.index(value)
            defaultCategory = category_ids[defaultCategoryID]
            break
        else:
            defaultCategory = None
            category_name = ''
            categories_ids = []
            continue

    main_category_id = int(MCategory)

    # Validating categories_ids data
    try:
        if defaultCategory == main_category_id:
            categories_ids = [main_category_id]
            categories_json = {"id": main_category_id,
                               "enabled": True}
        elif not defaultCategory:
            categories_ids = [main_category_id]
            categories_json = {"id": main_category_id,
                               "enabled": True}
        else:
            categories_ids = [main_category_id, defaultCategory]
            categories_json = {"id": main_category_id,
                               "enabled": True}, {"id": defaultCategory,
                                                  "enabled": True}

    except Exception as e:
        logger.exception(f"Category filling error occurred: {e}")
        defaultCategory = main_category_id
        categories_ids = [main_category_id]
        # noinspection PyDictDuplicateKeys
        categories_json = {"id": main_category_id,
                           "enabled": True}
    logger.info("Category filling is done")
    return category_name, categories_ids, main_category_id, categories_json

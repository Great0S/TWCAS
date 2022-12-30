from config.settings import settings

logger = settings.logger

def category_processor(telegram_category, categories, MCategory):
    default_category_ID = default_category_name = default_category_name_en = None
    try:
        for value in categories:
            for item in value:
                if item['nameTranslated']['ar'] == telegram_category and item['parentId'] == MCategory:
                    default_category_name = telegram_category
                    default_category_name_en = item['name']
                    default_category_ID = item['id']
                    break
                else:
                    continue
                
        if default_category_name:
            logger.info(
                f"Category processed successfully | Arabic: {default_category_name} | English: {default_category_name_en}")
        else:
            logger.warning(
                f"Category {telegram_category} is not on the list")
        
        main_category_id = int(MCategory)
             
        if default_category_ID == main_category_id or not default_category_ID:
            categories_ids = [main_category_id]
            categories_json = {"id": main_category_id,
                               "enabled": True}
        else:
            categories_ids = [main_category_id, default_category_ID]
            categories_json = {"id": main_category_id,
                               "enabled": True}, {"id": default_category_ID,
                                                  "enabled": True}
        logger.info("Category filling is done")
        
    except Exception as e:
        logger.exception(f"Category filling error occurred: {e}")
        default_category_ID = main_category_id
        categories_ids = [main_category_id]
        categories_json = {"id": main_category_id,
                           "enabled": True}    
    
    return default_category_name, default_category_name_en, categories_ids, main_category_id, categories_json

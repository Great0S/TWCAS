from config.settings import settings

logger = settings.logger

async def feedback(session: str, arg: str, arg_type: str, alert):
    log = eval(f"logger.{arg_type}")
    log(arg)
    await alert.send_message(entity=settings.alert_channel_id, message=f"{session} | {arg}")
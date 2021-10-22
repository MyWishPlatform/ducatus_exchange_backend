import logging

from django.db import transaction

from ducatus_exchange.bot.models import BotSub, BotSwapMessage
from ducatus_exchange.start_bot_polling import Bot


logger = logging.getLogger('bot')


@transaction.atomic
def send_or_update_message(swap_id, state):
    subs = BotSub.objects.all()
    message = generate_message(swap_id, state)
    for sub in subs:
        try:
            message_model, created = BotSwapMessage.objects.select_for_update().get_or_create(
                swap_id=swap_id, sub=sub
            )
            if created:
                message_model.message_id = Bot.bot.send_message(sub.chat_id, message, parse_mode='html',
                                                                    disable_web_page_preview=True).message_id
                message_model.save()
            else:
                Bot.bot.edit_message_text(message, sub.chat_id, message_model.message_id, parse_mode='html',
                                                disable_web_page_preview=True)
        except Exception as e:
            logger.error(msg=f'send_or_update_message FAILED on payment: {swap_id} with exception: \n {e}')
    logger.info(msg=f'send_or_update_message SUCCEDED on payment: {swap_id}')


def generate_message(swap_id, state):
    return f'Payment: {swap_id} handled with status: {state}'

import logging

from django.db import transaction

from ducatus_exchange.bot.models import BotSub, BotSwapMessage
from ducatus_exchange.bot.base import Bot


logger = logging.getLogger('bot')


@transaction.atomic
def send_or_update_message(payment_id, state):
    subs = BotSub.objects.all()
    message = generate_message(payment_id, state)
    for sub in subs:
        try:
            message_model, created = BotSwapMessage.objects.select_for_update().get_or_create(
                payment_id=payment_id, sub=sub
            )
            if created:
                message_model.message_id = Bot().bot.send_message(sub.chat_id, message, parse_mode='html',
                                                                    disable_web_page_preview=True).message_id
                message_model.save()
            else:
                Bot().bot.edit_message_text(message, sub.chat_id, message_model.message_id, parse_mode='html',
                                                disable_web_page_preview=True)
        except Exception as e:
            logger.error(msg=f'send_or_update_message FAILED on payment: {payment_id} with exception: \n {e}')
    logger.info(msg=f'send_or_update_message SUCCEDED on payment: {payment_id}')


def generate_message(payment, state):
    ('WAITING_FOR_TRANSFER', 'DONE', 'ERROR', 'RETURNED', 'IN_QUEUE', 'IN_PROCESS')
    if payment.state == 'WAITING_FOR_TRANSFER':
        'waiting for tranfser'

def generate_message(payment_id, state):
    return f'Payment: {payment_id} handled with status: {state}'

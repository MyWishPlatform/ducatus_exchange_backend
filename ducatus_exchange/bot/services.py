import logging

from django.db import transaction
from urllib.parse import urljoin
from ducatus_exchange.bot.models import BotSub, BotSwapMessage
from ducatus_exchange.bot.base import Bot
from ducatus_exchange.settings import NETWORK_SETTINGS


logger = logging.getLogger('bot')


@transaction.atomic
def send_or_update_message(payment):
    subs = BotSub.objects.all()
    message = generate_message(payment)
    for sub in subs:
        try:
            message_model, created = BotSwapMessage.objects.select_for_update().get_or_create(
                payment_id=payment.id, sub=sub
            )
            if created:
                message_model.message_id = Bot().bot.send_message(sub.chat_id, message, parse_mode='html',
                                                                    disable_web_page_preview=True).message_id
                message_model.save()
            else:
                Bot().bot.edit_message_text(message, sub.chat_id, message_model.message_id, parse_mode='html',
                                                disable_web_page_preview=True)
        except Exception as e:
            logger.error(msg=f'send_or_update_message FAILED on payment: {payment.id} with exception: \n {e}')
    logger.info(msg=f'send_or_update_message SUCCEDED on payment: {payment.id}')


def generate_message(payment):
    hyperlink = '<a href="{url}">{text}</a>'
    from_network = NETWORK_SETTINGS[payment.currency]
    from_symbol = from_network['currency']
    from_amount = f'{payment.original_amount / (10 ** from_network["decimals"])} {from_symbol}'
    from_tx_url = urljoin(from_network['explorer_url'], 'tx', payment.from_tx_hash)
    from_tx_hyperlinked = hyperlink.format(url=from_tx_url, text=from_amount)

    if payment.state == 'WAITING_FOR_TRANSFER':
        return f'received: {from_tx_hyperlinked}'
    elif payment.state == 'IN_PROCESS':
        return f'in process: {from_tx_hyperlinked}'
    elif payment.state == 'IN_QUEUE':
        return f'in queue: {from_tx_hyperlinked}'
    elif payment.state == 'RETURNED':
        return f'returned: {from_tx_hyperlinked}'
    elif payment.state == 'DONE':
        return f'success: {from_tx_hyperlinked}'
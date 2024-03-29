import logging

from django.db import transaction
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
                payment_id=payment.id, sub=sub,
            )
            if created:
                message_model.message_id = Bot().bot.send_message(
                    sub.chat_id, 
                    message, 
                    parse_mode='html', 
                    disable_web_page_preview=True
                ).message_id
                message_model.save()
            else:
                Bot().bot.edit_message_text(
                    message, 
                    sub.chat_id, 
                    message_model.message_id, 
                    parse_mode='html',
                    disable_web_page_preview=True
                )
        except Exception as e:
            logger.error(msg=f'send_or_update_message FAILED on payment: {payment.id} with exception: \n {e}')
    logger.info(msg=f'send_or_update_message SUCCEDED on payment: {payment.id}')


def generate_message(payment):
    hyperlink = '<a href="{url}">{text}</a>'

    currency = payment.currency
    if currency in ['USDT', 'USDC']:
        currency = 'ETH'

    from_network = NETWORK_SETTINGS[currency]
    from_amount = f'{payment.original_amount / (10 ** from_network["decimals"])} {payment.currency}'
    from_tx_url = from_network['explorer_url'] + '/'.join(['tx', payment.tx_hash])
    from_tx_hyperlinked = hyperlink.format(url=from_tx_url, text=from_amount)

    if payment.transfer_state == 'WAITING_FOR_TRANSFER':
        return f'received: {from_tx_hyperlinked}'
    elif payment.transfer_state == 'QUEUED':
        return f'queued: {from_tx_hyperlinked}'
    elif payment.transfer_state == 'RETURNED':
        return_tx_url = from_network['explorer_url'] + '/'.join(['tx', payment.returned_tx_hash])
        return_tx_hyperlinked = hyperlink.format(url=return_tx_url, text=from_amount)
        return f'returned: {from_tx_hyperlinked} → {return_tx_hyperlinked}'
    else:
        transfer = payment.transfers.first()
        to_network = NETWORK_SETTINGS[transfer.currency]
        to_amount = f'{transfer.amount / (10 ** to_network["decimals"])} {transfer.currency}'
        to_tx_url = to_network['explorer_url'] + '/'.join(['tx', transfer.tx_hash])
        to_tx_hyperlinked = hyperlink.format(url=to_tx_url, text=to_amount)
        if payment.transfer_state == 'PENDING':
            return f'pending: {from_tx_hyperlinked} → {to_tx_hyperlinked}'
        elif payment.transfer_state == 'DONE':
            return f'success: {from_tx_hyperlinked} → {to_tx_hyperlinked}'
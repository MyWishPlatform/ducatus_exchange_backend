from django.db import models
from django_fsm import FSMField, transition

from ducatus_exchange.bot.services import send_or_update_message
from ducatus_exchange.consts import MAX_DIGITS
from ducatus_exchange.exchange_requests.models import ExchangeRequest


class Payment(models.Model):
    """
    Model which store information about user payments

    Can link to tx_hash or Charge object, depending on what type of payment user choose
    """

    TRANSFER_STATES_DEFAULT = ('WAITING_FOR_TRANSFER', 'DONE', 'ERROR', 'RETURNED', 'IN_QUEUE', 'IN_PROCESS')
    COLLECTION_STATES_DEFAULT = ('NOT_COLLECTED', 'COLLECTED', 'ERROR')
    TRANSFER_STATES = list(zip(TRANSFER_STATES_DEFAULT, TRANSFER_STATES_DEFAULT))
    COLLECTION_STATES = list(zip(COLLECTION_STATES_DEFAULT, COLLECTION_STATES_DEFAULT))

    exchange_request = models.ForeignKey(ExchangeRequest, on_delete=models.CASCADE, null=True)
    charge = models.ForeignKey('quantum.Charge', on_delete=models.CASCADE, null=True)
    tx_hash = models.CharField(max_length=100, null=True, default='')
    currency = models.CharField(max_length=50, null=True, default='')
    original_amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    rate = models.DecimalField(max_digits=512, decimal_places=0)
    sent_amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    created_date = models.DateTimeField(auto_now_add=True)
    transfer_state = FSMField(default=TRANSFER_STATES_DEFAULT[0], choices=TRANSFER_STATES)
    collection_state = FSMField(default=COLLECTION_STATES_DEFAULT[0], choices=COLLECTION_STATES)
    collection_tx_hash = models.CharField(max_length=100, null=True, default='')
    returned_tx_hash = models.CharField(max_length=100, null=True, default='')

    # States change
    @transition(field=transfer_state, source=['WAITING_FOR_TRANSFER', 'ERROR'], target='DONE')
    def state_transfer_done(self):
        send_or_update_message(self.tx_hash, self.transfer_state)

    @transition(field=transfer_state, source='*', target='ERROR')
    def state_transfer_error(self):
        send_or_update_message(self.tx_hash, self.transfer_state)
        print('Transfer not completed, reverting payment', flush=True)

    @transition(field=transfer_state, source='*', target='RETURNED')
    def state_transfer_returned(self):
        send_or_update_message(self.tx_hash, self.transfer_state)

    @transition(field=transfer_state, source='*', target='IN_QUEUE')
    def state_transfer_in_queue(self):
        send_or_update_message(self.tx_hash, self.transfer_state)

    @transition(field=transfer_state, source=['IN_QUEUE',], target='IN_PROCESS')
    def state_transfer_in_process(self):
        send_or_update_message(self.tx_hash, self.transfer_state)

    @transition(field=collection_state, source=['NOT_COLLECTED', 'ERROR'], target='COLLECTED')
    def state_collect_duc(self):
        pass

    @transition(field=collection_state, source='*', target='ERROR')
    def state_error_collect_duc(self):
        pass

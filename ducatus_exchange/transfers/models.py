from django.db import models

from ducatus_exchange.consts import MAX_DIGITS
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.exchange_requests.models import ExchangeRequest
from django_fsm import FSMField, transition


class DucatusTransfer(models.Model):
    STATES = ('DONE', 'WAITING_FOR_CONFIRMATION')
    exchange_request = models.ForeignKey(ExchangeRequest, on_delete=models.CASCADE, null=True)
    tx_hash = models.CharField(max_length=100, null=True, default='')
    amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    currency = models.CharField(max_length=25, null=True, default=None)
    state = FSMField(default='', choices=STATES)
    created_date = models.DateTimeField(auto_now_add=True)

    # States change
    @transition(field=state, source='*', target='DONE')
    def state_done(self):
        pass

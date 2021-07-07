from django.db import models

from ducatus_exchange.vouchers.models import Voucher
from ducatus_exchange.consts import MAX_DIGITS


class Transfer(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, null=True)
    duc_amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    tx_hash = models.CharField(max_length=100, null=True, default=None)
    duc_address = models.CharField(max_length=50)
    transfer_status = models.CharField(max_length=50, default='WAITING_FOR_TRANSFER')
    vout_number = models.IntegerField(null=True, default=None)
    tag = models.CharField(max_length=50, null=True, default=None)

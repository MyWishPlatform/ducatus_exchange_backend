from django.db import models

from ducatus_widget.consts import MAX_DIGITS
from ducatus_widget.payments.models import Payment


class DucatusTransfer(models.Model):
    user_address = models.CharField(max_length=100, null=True, default='')
    tx_hash = models.CharField(max_length=100, null=True, default='')
    amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    rate = models.DecimalField(max_digits=512, decimal_places=0)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)

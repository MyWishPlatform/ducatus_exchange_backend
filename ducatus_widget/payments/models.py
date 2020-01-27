from django.db import models
from django.contrib.auth.models import User

from ducatus_widget.consts import MAX_DIGITS


class Payment(models.Model):
    user_address = models.CharField(max_length=100, null=True, default='')
    tx_hash = models.CharField(max_length=100, null=True, default='')
    currency = models.CharField(max_length=50, null=True, default='')
    original_amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    rate = models.DecimalField(max_digits=512, decimal_places=0)
    sent_amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)

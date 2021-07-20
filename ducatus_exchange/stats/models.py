from django.db import models

from ducatus_exchange.consts import MAX_DIGITS


class DucatusAddressBlacklist(models.Model):
    duc_wallet_address = models.CharField(max_length=64, help_text='corporate duc wallets', default='', unique=True)
    ducx_wallet_address = models.CharField(max_length=64, help_text='corporate ducx wallets', default='', unique=True)


class BitcoreAddress(models.Model):
    user_address = models.CharField(max_length=100, unique=True)
    balance = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0, null=True, default=0)


class StatisticsAddress(models.Model):
    user_address = models.CharField(max_length=100, unique=True)
    balance = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0, null=True, default=0)
    network = models.CharField(max_length=100)


class StatisticsTransfer(models.Model):
    transaction_value = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    transaction_time = models.DateTimeField()
    tx_hash = models.CharField(max_length=256, null=True, default='')
    currency = models.CharField(max_length=10)
    address_from = models.ForeignKey(StatisticsAddress, on_delete=models.CASCADE,
                                     related_name='address_from', null=True, default=None)
    address_to = models.ForeignKey(StatisticsAddress, on_delete=models.CASCADE,
                                   related_name='address_to', null=True, default=None)
    fee_amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0, default=0)

import secrets

from django.db import models

from ducatus_exchange.consts import MAX_DIGITS
from ducatus_exchange.freezing.models import CltvDetails
from ducatus_exchange.exchange_requests.views import register_voucher_in_lottery


class FreezingVoucher(models.Model):
    wallet_id = models.CharField(max_length=50)
    cltv_details = models.OneToOneField(CltvDetails, null=True, default=None, on_delete=models.CASCADE)
    user_duc_address = models.CharField(max_length=50)


class Voucher(models.Model):
    voucher_code = models.CharField(max_length=50, unique=True)
    activation_code = models.CharField(max_length=50, unique=True, default=secrets.token_urlsafe)
    usd_amount = models.FloatField()
    is_active = models.BooleanField(default=True)
    is_used = models.BooleanField(default=False)
    publish_date = models.DateTimeField(auto_now_add=True)
    activation_date = models.DateTimeField(null=True, default=None)
    lock_days = models.IntegerField(default=0)
    freezing_details = models.OneToOneField(
        FreezingVoucher,
        on_delete=models.SET_NULL,
        null=True, default=None,
        related_name='voucher'
    )
    # Filled only if it was created by card payment. If yes, it will register in lottery
    charge_id = models.IntegerField(null=True)
    payment_id = models.IntegerField(null=True, default=None)

    def register_in_lottery(self, transfer):
        print(f'Try to register Voucher {self.id} in lottery', flush=True)
        data = {
            "charge_id": self.charge_id,
            "payment_id": self.payment_id,
            "transfer": {
                "duc_address": transfer.duc_address,
                "tx_hash": transfer.tx_hash,
                "amount": int(transfer.duc_amount),
            },
        }

        register_voucher_in_lottery(data=data)


class VoucherInput(models.Model):
    voucher = models.ForeignKey(FreezingVoucher, on_delete=models.CASCADE)
    tx_vout = models.IntegerField()
    mint_tx_hash = models.CharField(max_length=100)
    spent_tx_hash = models.CharField(max_length=100, null=True, default=None)
    amount = models.DecimalField(max_digits=MAX_DIGITS, decimal_places=0)
    minted_at = models.DateTimeField(auto_now_add=True)
    spent_at = models.DateTimeField(null=True, default=None)


class UnlockVoucherTx(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    tx_hash = models.CharField(max_length=100, unique=True)

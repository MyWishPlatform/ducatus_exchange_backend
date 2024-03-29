from django.db import models

from ducatus_exchange.payments.models import Payment


class QuantumAccount(models.Model):
    account_id = models.IntegerField()
    address = models.CharField(max_length=50)
    access_token = models.TextField(null=True)
    token_type = models.CharField(max_length=20, null=True)
    token_expires_at = models.BigIntegerField(null=True)


class Charge(models.Model):
    charge_id = models.IntegerField(unique=True)
    status = models.CharField(max_length=50)
    currency = models.CharField(max_length=10)
    amount = models.IntegerField()
    hash = models.CharField(max_length=100)
    redirect_url = models.CharField(max_length=200)
    email = models.CharField(max_length=50)

    def create_payment(self, sent_amount, rate):
        payment = Payment(
            charge=self,
            currency=self.currency,
            original_amount=self.amount,
            rate=rate,
            sent_amount=sent_amount
        )
        payment.save()
        return payment

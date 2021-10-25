from django.db import models
# from ducatus_exchange.payments.models import Payment


class BotSub(models.Model):
    chat_id = models.IntegerField(unique=True)


class BotSwapMessage(models.Model):
    swap = models.ForeignKey('ducatus_exchange.payments.Payment', on_delete=models.CASCADE)
    sub = models.ForeignKey(BotSub, on_delete=models.CASCADE)
    message_id = models.IntegerField(default=0)

    class Meta:
        unique_together = (('swap_id', 'sub_id'),)

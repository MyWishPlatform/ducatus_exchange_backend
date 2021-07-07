from rest_framework import serializers

from ducatus_exchange.freezing.models import CltvDetails


class CltvDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CltvDetails
        fields = ('withdrawn', 'lock_time', 'redeem_script', 'locked_duc_address', 'user_public_key', 'frozen_at',
                  'private_path')

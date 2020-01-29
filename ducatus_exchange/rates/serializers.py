from rest_framework import serializers

'''
{
    "price": {
        "BTC": "431.23550000",
        "ETH": "8.30200000"
    },
    "rate": {
        "BTC": "0.00000580",
        "ETH": "0.00030115"
    }
}
'''


class RateSerializer(serializers.Serializer):
    BTC = serializers.FloatField()
    ETH = serializers.FloatField()


class PriceSerializer(serializers.Serializer):
    BTC = serializers.FloatField()
    ETH = serializers.FloatField()


class ExchangeSerializer(serializers.Serializer):
    price = PriceSerializer()
    rate = RateSerializer()





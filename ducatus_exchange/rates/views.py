from rest_framework.views import APIView
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ducatus_exchange.rates.api import get_usd_rates, get_usd_prices, convert_to_duc_single
from ducatus_exchange.rates.serializers import ExchangeSerializer, RateSerializer, PriceSerializer

#rate_path = openapi.Parameter('')

class RateRequest(APIView):

    @swagger_auto_schema(
        operation_description="rate and price request",
        responses={200: ExchangeSerializer()},
        manual_parameters=[]
    )
    def get(self, request):
        usd_rate = get_usd_rates()
        usd_price = get_usd_prices()

        comb_data = {
            'rate': convert_to_duc_single(usd_rate),
            'price': convert_to_duc_single(usd_price)
        }

        res = ExchangeSerializer(comb_data)
        return Response(res.data)
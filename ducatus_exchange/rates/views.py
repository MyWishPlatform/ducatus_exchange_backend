from rest_framework.views import APIView
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ducatus_exchange.rates.api import get_usd_rates, get_usd_prices, convert_to_duc_single
from ducatus_exchange.rates.serializers import AllRatesSerializer

#rate_path = openapi.Parameter('')

class RateRequest(APIView):

    @swagger_auto_schema(
        operation_description="rate and price request",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['to_currency'],
            properties={
                'to_currency': openapi.Schema(type=openapi.TYPE_STRING)
            },
        ),
        responses={200: AllRatesSerializer()},
    )
    def get(self, request):
        usd_price = get_usd_prices()
        data = {}

        res = AllRatesSerializer(data)

        return Response(res.data)

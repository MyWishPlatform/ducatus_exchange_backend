from rest_framework.views import APIView
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ducatus_exchange.rates.serializers import AllRatesSerializer

rates_response = openapi.Response(
    description='ETH, BTC, DUCX rates for DUC, DUC rate for DUCX',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'DUC': openapi.Schema(type=openapi.TYPE_OBJECT,
                                  properties={
                                      'ETH': openapi.Schema(type=openapi.TYPE_STRING),
                                      'BTC': openapi.Schema(type=openapi.TYPE_STRING),
                                      'DUCX': openapi.Schema(type=openapi.TYPE_STRING)
                                      },
                                  ),
            'DUCX': openapi.Schema(type=openapi.TYPE_OBJECT,
                                   properties={
                                      'DUC': openapi.Schema(type=openapi.TYPE_STRING)
                                      },
                                   ),
        },
    )
)


class RateRequest(APIView):
    @swagger_auto_schema(
        operation_description="rate request",
        responses={200: rates_response}
    )
    def get(self, request):
        data = {}

        res = AllRatesSerializer(data)

        return Response(res.data)

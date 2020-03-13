from rest_framework.views import APIView
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ducatus_exchange.rates.serializers import AllRatesSerializer


class RateRequest(APIView):

    @swagger_auto_schema(
        operation_description="rate and price request",
        responses={200: AllRatesSerializer()}
    )
    def get(self, request):
        data = {}

        res = AllRatesSerializer(data)

        return Response(res.data)

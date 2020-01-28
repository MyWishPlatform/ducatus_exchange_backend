from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# from ducatus_widget.exchange_requests.api import get_usd_rates, get_usd_prices, convert_to_duc_single
from ducatus_widget.exchange_requests.serializers import ExchangeRequestSerializer


class ExchangeRequest(APIView):

    @swagger_auto_schema(
        operation_description="post DUC address and get ETH and BTC addresses for payment",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['duc_address'],
            properties={
                'duc_address': openapi.Schema(type=openapi.TYPE_STRING)
            },
        ),
        responses={200: ExchangeRequestSerializer()},

    )
    def post(self, request):
        print(request.data)
        serializer = ExchangeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


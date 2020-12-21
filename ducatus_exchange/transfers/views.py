import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ducatus_exchange.exchange_requests.models import DucatusUser, ExchangeRequest
from ducatus_exchange.consts import DAYLY_LIMIT, WEEKLY_LIMIT


check_limit_response = openapi.Response(
    description='Response with available limits',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            #'ducx_address': openapi.Schema(type=openapi.TYPE_STRING),
            'dayly_available': openapi.Schema(type=openapi.TYPE_NUMBER),
            'weekly_available': openapi.Schema(type=openapi.TYPE_NUMBER),
        },
    )
)

class CheckLimitView(APIView):

    @swagger_auto_schema(
        operation_description="post address to check limits",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['address'],
            properties={
                'address': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={200: check_limit_response},

    )
    def post(self, request):
        request_data = request.data
        print('request data:', request_data, flush=True)
        address = request_data.get('address')
        ducatus_user = DucatusUser.objects.filter(address = address).last()
        exchange_request = ExchangeRequest.objects.get(user=ducatus_user)
        dayly_available = DAYLY_LIMIT - exchange_request.dayly_swap
        weekly_available = WEEKLY_LIMIT - exchange_request.weekly_swap


        response_data = {'daily_available': dayly_available, 'weekly_available': weekly_available}

        print('res:', response_data)

        return Response(response_data, status=status.HTTP_200_OK)

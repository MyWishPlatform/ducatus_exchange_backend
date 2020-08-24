from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ducatus_exchange.exchange_requests.models import DucatusUser, ExchangeRequest

from ducatus_exchange.litecoin_rpc import DucatuscoreInterface

exchange_response_duc = openapi.Response(
    description='Response with ETH, BTC, DUCX addresses if `DUC` passed in `to_currency`',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'ducx_address': openapi.Schema(type=openapi.TYPE_STRING),
            'btc_address': openapi.Schema(type=openapi.TYPE_STRING),
            'eth_address': openapi.Schema(type=openapi.TYPE_STRING),
        },
    )
)

exchange_response_ducx = openapi.Response(
    description='Response with DUC addresses if `DUCX` passed in `to_currency`',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'duc_address': openapi.Schema(type=openapi.TYPE_STRING)
        },
    )
)

validate_address_result = openapi.Response(
    description='Response with status of validated address',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'address_valid': openapi.Schema(type=openapi.TYPE_BOOLEAN)
        },
    )
)


class ExchangeRequestView(APIView):

    @swagger_auto_schema(
        operation_description="post DUC or DUCX address and get addresses for payment",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['to_address', 'to_currency', 'email'],
            properties={
                'to_address': openapi.Schema(type=openapi.TYPE_STRING),
                'to_currency': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={200: exchange_response_duc, 201: exchange_response_ducx},

    )
    def post(self, request):
        request_data = request.data
        print('request data:', request_data, flush=True)
        address = request_data.get('to_address')
        platform = request_data.get('to_currency')
        email = request_data.get('email')

        if address is None:
            return Response({'error': 'to_address not passed'}, status=status.HTTP_400_BAD_REQUEST)
        if platform is None:
            return Response({'error': 'to_platform not passed'}, status=status.HTTP_400_BAD_REQUEST)

        ducatus_user, exchange_request = get_or_create_ducatus_user_and_exchange_request(
            request, address, platform, email
        )

        if platform == 'DUC':
            response_data = {
                'eth_address': exchange_request.eth_address,
                'btc_address': exchange_request.btc_address,
                'ducx_address': exchange_request.ducx_address
            }
        else:
            response_data = {'duc_address': exchange_request.duc_address}
            # response_data = {}

        print('res:', response_data)

        return Response(response_data, status=status.HTTP_201_CREATED)


class ValidateDucatusAddress(APIView):
    @swagger_auto_schema(
        operation_description="post DUC address to validate",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['to_address'],
            properties={
                'address': openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={200: validate_address_result},

    )
    def post(self, request):
        address = request.data.get('address')

        rpc = DucatuscoreInterface()
        valid = rpc.validate_address(address)

        return Response({'address_valid': valid}, status=status.HTTP_200_OK)


def get_or_create_ducatus_user_and_exchange_request(request, address, platform, email):
    ducatus_user_filter = DucatusUser.objects.filter(address=address, platform=platform)
    if not ducatus_user_filter:
        # Create user
        ducatus_user = DucatusUser(address=address, platform=platform, email=email)
        ducatus_user.save()
        # And create ER
        exchange_request = ExchangeRequest(user=ducatus_user)
        exchange_request.save()
        exchange_request.generate_keys()
        exchange_request.save()
    else:
        # Else just get them from db
        ducatus_user = ducatus_user_filter.last()
        exchange_request = ExchangeRequest.objects.get(user=ducatus_user)
        if email:
            ducatus_user.email = email
            ducatus_user.save()
    print('addresses:', exchange_request.__dict__, flush=True)

    ref_address = request.COOKIES.get('referral')
    print('REF ADDRESS', ref_address, flush=True)
    if ref_address and ref_address != ducatus_user.address:
        ducatus_user.ref_address = ref_address
        ducatus_user.save()
        print('REF ADDRESS', ref_address, flush=True)

    return ducatus_user, exchange_request

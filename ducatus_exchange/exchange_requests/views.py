import datetime
import logging

# from rest_framework.generics import RetrieveAPIView
from rest_framework.viewsets import ModelViewSet

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ducatus_exchange.exchange_requests.models import DucatusUser, ExchangeRequest, ExchangeStatus
from ducatus_exchange.exchange_requests.serializers import ExchangeStatusSerializer
from ducatus_exchange.litecoin_rpc import DucatuscoreInterface
from ducatus_exchange.quantum.models import Charge
from ducatus_exchange.transfers.serializers import DucatusTransferSerializer
from ducatus_exchange.lottery.api import LotteryRegister
from ducatus_exchange.payments.models import Payment


logger = logging.getLogger(__name__)


exchange_response_duc = openapi.Response(
    description='Response with ETH, BTC, DUCX addresses if `DUC` passed in `to_currency`',
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'ducx_address': openapi.Schema(type=openapi.TYPE_STRING),
            'btc_address': openapi.Schema(type=openapi.TYPE_STRING),
            'eth_address': openapi.Schema(type=openapi.TYPE_STRING),
            'usdc_address': openapi.Schema(type=openapi.TYPE_STRING),
            'usdt_address': openapi.Schema(type=openapi.TYPE_STRING),
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
        logger.info(msg=('request data:', request_data))
        address = request_data.get('to_address', f'voucher_{datetime.datetime.now().timestamp()}')
        platform = request_data.get('to_currency')
        email = request_data.get('email')

        ducatus_user, exchange_request = get_or_create_ducatus_user_and_exchange_request(
            request, address, platform, email
        )

        if platform == 'DUC':
            response_data = {
                'eth_address': exchange_request.eth_address,
                'btc_address': exchange_request.btc_address,
                'ducx_address': exchange_request.ducx_address,
                'usdc_address': exchange_request.eth_address,
                'usdt_address': exchange_request.eth_address,
            }
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)
           # response_data = {'duc_address': exchange_request.duc_address}

        logger.info(msg=('res:', response_data))

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


def get_or_create_ducatus_user_and_exchange_request(request, address, platform, email=None):
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
    logger.info(msg=('addresses:', exchange_request.__dict__))

    ref_address = request.COOKIES.get('referral')
    logger.info(msg=('REF ADDRESS', ref_address))
    if ref_address and ref_address != ducatus_user.address:
        ducatus_user.ref_address = ref_address
        ducatus_user.save()
        logger.info(msg=('REF ADDRESS', ref_address))

    return ducatus_user, exchange_request


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'charge_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'transfer': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "duc_address": openapi.Schema(type=openapi.TYPE_STRING),
                    "tx_hash": openapi.Schema(type=openapi.TYPE_STRING),
                    "amount": openapi.Schema(type=openapi.TYPE_INTEGER),
                }
            ),
        },
    ),
)
@api_view(http_method_names=['POST'])
def register_voucher_in_lottery(request: Request):
    """
    Allows to register voucher in lottery.

    Cause of splitted logic of ducatus_exchange and ducatus_voucher,
    it cannot be done easier. After merging this two backends this workflow should be simplify
    """
    platform = 'DUC'
    # Get values from request
    charge_id = request.data.get('charge_id')
    payment_id = request.data.get('payment_id')
    transfer_dict = request.data.get('transfer', {})
    duc_address = transfer_dict.get('duc_address')

    if charge_id:
        charge = Charge.objects.get(charge_id=charge_id)
        email = charge.email
        payment = Payment.objects.get(charge__charge_id=charge_id)
        _, exchange_request = get_or_create_ducatus_user_and_exchange_request(request, duc_address, platform, email)
        exchange_request.save()
    elif payment_id:
        payment = Payment.objects.get(id=payment_id)
        exchange_request = payment.exchange_request
        exchange_request.user.save()
    else:
        raise ValidationError

    # Prepare values for create transfer object
    transfer_dict['exchange_request'] = exchange_request.id
    transfer_dict['payment'] = payment.id
    transfer_dict['currency'] = platform
    transfer_dict['state'] = 'DONE'

    # Validate and save transfer
    transfer_serializer = DucatusTransferSerializer(data=transfer_dict)
    transfer_serializer.is_valid(raise_exception=True)
    transfer = transfer_serializer.save()

    # Fill payment exchange request
    payment.exchange_request = exchange_request
    payment.save()

    transfer.payment = payment
    transfer.save()

    # Register all prepared values in lottery
    lottery_entrypoint = LotteryRegister(transfer)
    lottery_entrypoint.try_register_to_lotteries()

    return Response(200)


@api_view(http_method_names=['GET'])
def total_id_count(request):
    return Response(ExchangeRequest.objects.all().last().id, status=status.HTTP_200_OK)


@api_view(http_method_names=['GET'])
def status_check(request):
    return Response(ExchangeStatus.objects.all().first().status, status=status.HTTP_200_OK)


class ExchangeStatusView(APIView):
    @swagger_auto_schema(
        operation_description="Get advanced status info",
        responses={
            200: ExchangeStatusSerializer()
        },
    )
    def get(self, request):
        status = ExchangeStatus.objects.first()
        serializer = ExchangeStatusSerializer(status)
        return Response(serializer.data)

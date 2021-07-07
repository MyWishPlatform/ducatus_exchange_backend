import requests
from django.db.utils import IntegrityError

from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from ducatus_exchange.vouchers.models import Voucher, FreezingVoucher
from ducatus_exchange.vouchers.serializers import VoucherSerializer, FreezingVoucherSerializer
from ducatus_exchange.freezing.api import get_unused_frozen_vouchers
from ducatus_exchange.litecoin_rpc import DucatuscoreInterface, JSONRPCException, DucatuscoreInterfaceException
from ducatus_exchange.vouchers.models import UnlockVoucherTx
from ducatus_exchange.vtransfers.api import validate_voucher
from ducatus_exchange.vtransfers.api import convert_usd2duc
from ducatus_exchange.settings import API_KEY_VOUCHER, DUC_CREDIT_CREDENTIALS, RATES_API_CHANGE_URL, RATES_API_CHANGE_KEY


class VoucherViewSet(viewsets.ModelViewSet):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'voucher_code': openapi.Schema(type=openapi.TYPE_STRING),
                'usd_amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'lock_days': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            required=['voucher_code', 'usd_amount']
        ),
        responses={200: VoucherSerializer()},
    )
    def create(self, request: Request, *args, **kwargs):
        if isinstance(request.data, list):
            voucher_list = request.data
            for voucher in voucher_list:
                serializer = self.get_serializer(data=voucher)
                if serializer.is_valid():
                    self.perform_create(serializer)
                else:
                    raise ValidationError(detail={'description': serializer.errors, 'voucher': voucher})
            return Response({'success': True}, status=status.HTTP_201_CREATED)
        else:
            return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'voucher_code': openapi.Schema(type=openapi.TYPE_STRING),
                'usd_amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'lock_days': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            required=['voucher_code', 'usd_amount']
        ),
        responses={200: VoucherSerializer()},
    )
    def update(self, request: Request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


@swagger_auto_schema(
    method='get',
    manual_parameters=[openapi.Parameter('voucher_id', openapi.IN_QUERY, type=openapi.TYPE_STRING)],
    responses={200: FreezingVoucherSerializer()},
)
@api_view(http_method_names=['GET'])
def get_withdraw_info(request: Request):
    voucher_id = request.query_params.get('voucher_id')

    try:
        frozen_voucher = FreezingVoucher.objects.get(id=voucher_id)
    except FreezingVoucher.DoesNotExist:
        raise NotFound

    response_data = FreezingVoucherSerializer().to_representation(frozen_voucher)

    return Response(response_data)


@swagger_auto_schema(
    method='get',
    manual_parameters=[openapi.Parameter('wallet_ids', openapi.IN_QUERY, type=openapi.TYPE_ARRAY,
                                         items=openapi.Items(type=openapi.TYPE_STRING))],
    responses={200: FreezingVoucherSerializer()},
)
@api_view(http_method_names=['GET'])
def get_frozen_vouchers(request: Request):
    wallet_ids = request.query_params.get('wallet_ids').split(',')

    unused_frozen_vouchers = get_unused_frozen_vouchers(wallet_ids)
    response_data = FreezingVoucherSerializer(many=True).to_representation(unused_frozen_vouchers)

    return Response(response_data)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'raw_tx_hex': openapi.Schema(type=openapi.TYPE_STRING),
        },
        required=['raw_tx_hex']
    ),
)
@api_view(http_method_names=['POST'])
def send_raw_transaction(request):
    raw_tx_hex = request.data.get('raw_tx_hex')

    try:
        interface = DucatuscoreInterface()
        tx_hash = interface.rpc.sendrawtransaction(raw_tx_hex)
        print('unlock tx hash', tx_hash, flush=True)
        unlock_tx = UnlockVoucherTx(tx_hash=tx_hash)
        unlock_tx.save()
    except IntegrityError:
        raise PermissionDenied(detail='-27: transaction already in block chain')
    except JSONRPCException as err:
        raise PermissionDenied(detail=str(err))

    return Response({'success': True, 'tx_hash': tx_hash})


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'api_key': openapi.Schema(type=openapi.TYPE_STRING),
            'voucher_code': openapi.Schema(type=openapi.TYPE_STRING),
            'usd_amount': openapi.Schema(type=openapi.TYPE_INTEGER),
            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            'lock_days': openapi.Schema(type=openapi.TYPE_INTEGER),
            'charge_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            'payment_id': openapi.Schema(type=openapi.TYPE_INTEGER),
        },
        required=['api_key', 'voucher_code', 'usd_amount']
    ),
    responses={200: VoucherSerializer()}
)
@api_view(http_method_names=['POST'])
def register_voucher(request: Request):
    api_key = request.data.get('api_key')
    if api_key != API_KEY_VOUCHER:
        raise PermissionDenied(detail='invalid api key')

    request.data.pop('api_key')
    voucher_data = request.data

    serializer = VoucherSerializer(data=voucher_data)
    if serializer.is_valid():
        serializer.save()
    else:
        raise ValidationError(detail={'description': serializer.errors, 'voucher': voucher_data})

    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    manual_parameters=[openapi.Parameter('api_key', openapi.IN_QUERY, type=openapi.TYPE_STRING),
                       openapi.Parameter('voucher_code', openapi.IN_QUERY, type=openapi.TYPE_STRING)],
)
@api_view(http_method_names=['GET'])
def get_voucher_activation_code(request: Request):
    api_key = request.query_params.get('api_key')
    if api_key != API_KEY_VOUCHER:
        raise PermissionDenied(detail='invalid api key')

    voucher_code = request.query_params.get('voucher_code')

    try:
        voucher = Voucher.objects.get(voucher_code=voucher_code)
    except Voucher.DoesNotExist:
        raise NotFound(detail=f'voucher with id {voucher_code} not found')

    voucher = validate_voucher(voucher.activation_code)

    response_data = {
        'voucher_code': voucher.voucher_code,
        'activation_code': voucher.activation_code,
    }

    return Response(response_data)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'client_id': openapi.Schema(type=openapi.TYPE_STRING),
            'client_secret': openapi.Schema(type=openapi.TYPE_STRING),
            'duc_address': openapi.Schema(type=openapi.TYPE_STRING),
            'usd_amount': openapi.Schema(type=openapi.TYPE_INTEGER),
        },
        required=['client_id', 'client_secret', 'duc_address', 'usd_amount']
    ),
)
@api_view(http_method_names=['POST'])
def credit_duc(request: Request):
    if request.data.get('client_id') != DUC_CREDIT_CREDENTIALS['client_id'] or \
            request.data.get('client_secret') != DUC_CREDIT_CREDENTIALS['client_secret']:
        raise PermissionDenied(detail='client_id or client_secret is invalid')

    duc_amount = convert_usd2duc(request.data.get('usd_amount'))
    rpc = DucatuscoreInterface()
    try:
        tx_hash = rpc.node_transfer(request.data.get('duc_address'), duc_amount)
    except DucatuscoreInterfaceException as err:
        raise ValidationError(detail=str(err))

    return Response({'success': True, 'tx_hash': tx_hash})


class ChangeDucRate(APIView):
    permission_classes = [IsAdminUser]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'DUC': openapi.Schema(type=openapi.TYPE_INTEGER),
                'DUCX': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            required=[]
        )
    )
    def post(self, request):
        post_data = request.data
        post_data['api-key'] = RATES_API_CHANGE_KEY

        res = requests.post(RATES_API_CHANGE_URL, data=post_data)
        return Response({'success': True, 'rates': res.json()})

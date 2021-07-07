from django.db.utils import IntegrityError

from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.decorators import api_view
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.exceptions import NotFound
from bitcoinrpc.authproxy import JSONRPCException

from ducatus_exchange.freezing.api import generate_cltv
from ducatus_exchange.freezing.models import CltvDetails
from ducatus_exchange.staking.models import UnlockDepositTx
from ducatus_exchange.staking.models import Deposit
from ducatus_exchange.staking.serializers import DepositSerializer
from ducatus_exchange.litecoin_rpc import DucatuscoreInterface
from ducatus_exchange.consts import DIVIDENDS_INFO


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'duc_address': openapi.Schema(type=openapi.TYPE_STRING),
            'duc_public_key': openapi.Schema(type=openapi.TYPE_STRING),
            'wallet_id': openapi.Schema(type=openapi.TYPE_STRING),
            'lock_months': openapi.Schema(type=openapi.TYPE_INTEGER),
            'private_path': openapi.Schema(type=openapi.TYPE_INTEGER),
        },
        required=['duc_address', 'duc_public_key', 'wallet_id', 'lock_months', 'private_path']
    ),
    responses={200: DepositSerializer()},
)
@api_view(http_method_names=['POST'])
def generate_deposit(request):
    duc_address = request.data.get('duc_address')
    user_public_key = request.data.get('duc_public_key')
    wallet_id = request.data.get('wallet_id')
    lock_months = request.data.get('lock_months')
    private_path = request.data.get('private_path')

    if lock_months not in DIVIDENDS_INFO:
        raise ValidationError('lock months must be in [5, 8, 13]')

    lock_days = CltvDetails.month_to_days(lock_months)
    cltv_details = generate_cltv(user_public_key, lock_days, private_path)

    deposit = Deposit()
    deposit.cltv_details = cltv_details
    deposit.wallet_id = wallet_id
    deposit.user_duc_address = duc_address
    deposit.dividends = DIVIDENDS_INFO[lock_months]
    deposit.save()

    response_data = DepositSerializer().to_representation(deposit)

    return Response(response_data)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'duc_address': openapi.Schema(type=openapi.TYPE_STRING),
            'receiver_user_public_key': openapi.Schema(type=openapi.TYPE_STRING),
            'sender_user_public_key': openapi.Schema(type=openapi.TYPE_STRING),
            'wallet_id': openapi.Schema(type=openapi.TYPE_STRING),
            'lock_days': openapi.Schema(type=openapi.TYPE_INTEGER),
            'private_path': openapi.Schema(type=openapi.TYPE_INTEGER),
        },
        required=['duc_address', 'receiver_user_public_key', 'sender_user_public_key',
                  'wallet_id', 'lock_days', 'private_path']
    ),
    responses={200: DepositSerializer()},
)
@api_view(http_method_names=['POST'])
def generate_deposit_without_dividends(request):
    duc_address = request.data.get('duc_address')
    receiver_user_public_key = request.data.get('receiver_user_public_key')
    sender_user_public_key = request.data.get('sender_user_public_key')
    wallet_id = request.data.get('wallet_id')
    lock_days = request.data.get('lock_days')
    private_path = request.data.get('private_path')

    cltv_details = generate_cltv(receiver_user_public_key, lock_days, private_path, sender_user_public_key)

    deposit = Deposit(
        cltv_details=cltv_details,
        wallet_id=wallet_id,
        user_duc_address=duc_address,
        dividends=0,
    )
    deposit.save()

    response_data = DepositSerializer().to_representation(deposit)
    return Response(response_data)


@swagger_auto_schema(
    method='get',
    manual_parameters=[openapi.Parameter('wallet_ids', openapi.IN_QUERY, type=openapi.TYPE_ARRAY,
                                         items=openapi.Items(type=openapi.TYPE_STRING))],
    responses={200: DepositSerializer()},
)
@api_view(http_method_names=['GET'])
def get_deposits(request):
    wallet_ids = request.query_params.get('wallet_ids').split(',')
    deposits = Deposit.objects.filter(wallet_id__in=wallet_ids, cltv_details__withdrawn=False)

    response_data = DepositSerializer(many=True).to_representation(deposits)

    return Response(response_data)


@swagger_auto_schema(
    method='get',
    manual_parameters=[openapi.Parameter('deposit_id', openapi.IN_QUERY, type=openapi.TYPE_STRING)],
    responses={200: DepositSerializer()},
)
@api_view(http_method_names=['GET'])
def get_deposit_info(request: Request):
    deposit_id = request.query_params.get('deposit_id')

    try:
        deposit = Deposit.objects.get(id=deposit_id)
    except Deposit.DoesNotExist:
        raise NotFound

    response_data = DepositSerializer().to_representation(deposit)

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
def send_deposit_transaction(request):
    raw_tx_hex = request.data.get('raw_tx_hex')

    try:
        interface = DucatuscoreInterface()
        tx_hash = interface.rpc.sendrawtransaction(raw_tx_hex)
        print('unlock tx hash', tx_hash, flush=True)
        unlock_tx = UnlockDepositTx(tx_hash=tx_hash)
        unlock_tx.save()
    except IntegrityError:
        raise PermissionDenied(detail='-27: transaction already in block chain')
    except JSONRPCException as err:
        raise PermissionDenied(detail=str(err))

    return Response({'success': True, 'tx_hash': tx_hash})

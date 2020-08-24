from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from ducatus_exchange.litecoin_rpc import DucatuscoreInterface
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.quantum.models import Charge
from ducatus_exchange.quantum.serializers import ChargeSerializer
from ducatus_exchange.rates.serializers import get_usd_prices
from ducatus_exchange.transfers.models import DucatusTransfer
from ducatus_exchange.exchange_requests.views import get_or_create_ducatus_user_and_exchange_request


@swagger_auto_schema(
    method='get',
    responses={200: ChargeSerializer()},
)
@api_view(http_method_names=['GET'])
def get_charge(request: Request, charge_id: int):
    try:
        charge = Charge.objects.get(charge_id=charge_id)
    except Charge.DoesNotExist:
        raise NotFound

    return Response(ChargeSerializer().to_representation(charge))


@swagger_auto_schema(
    method='post',
    reqcduest_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
            'currency': openapi.Schema(type=openapi.TYPE_STRING),
            'duc_address': openapi.Schema(type=openapi.TYPE_STRING),
            'email': openapi.Schema(type=openapi.TYPE_STRING),
        },
        required=['amount', 'currency', 'duc_address', 'email']
    ),
)
@api_view(http_method_names=['POST'])
def add_charge(request: Request):
    data = request.data

    duc_address = data.get('duc_address')
    email = data.get('email')
    platform = 'DUC'

    user, exchange_request = get_or_create_ducatus_user_and_exchange_request(
        request, duc_address, platform, email
    )
    data['exchange_request'] = exchange_request.id

    serializer = ChargeSerializer(data=data)
    if serializer.is_valid(raise_exception=True):
        serializer.save()

    return Response(serializer.data)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'type': openapi.Schema(type=openapi.TYPE_STRING),
            'data': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                }),
        },
    ),
)
@api_view(http_method_names=['POST'])
def change_charge_status(request: Request):
    if request.data['type'] == 'Charge':
        status = request.data['data']['status']
        charge_id = request.data['data']['id']
        if status == 'Charged':
            charge = Charge.objects.get(charge_id=charge_id)
            charge.status = status
            charge.save()

            # here should be transfer logic execution
            print(f'try transfer DUC for charge {charge_id}', flush=True)
            transfer_duc(charge.duc_address, charge.currency, charge.amount)


def transfer_duc(duc_address, original_curr, original_amount):
    # Calc rate and amount
    rates = get_usd_prices()
    duc_rate = rates['DUC']
    # TODO how to apply USD decimals?
    sent_amount = int(original_amount / float(duc_rate))

    # Create payment obj
    payment = Payment(
        currency=original_curr,
        original_amount=original_amount,
        rate=duc_rate,
        sent_amount=sent_amount
    )

    # Sent tx
    rpc = DucatuscoreInterface()
    tx = rpc.transfer(duc_address, original_amount)

    # Save tx
    transfer = DucatusTransfer(
        tx_hash=tx,
        amount=sent_amount,
        payment=payment,
        currency='DUC',
        state='WAITING_FOR_CONFIRMATION'
    )
    transfer.save()
    print('transfer saved', flush=True)

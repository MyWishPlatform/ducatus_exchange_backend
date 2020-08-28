from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from ducatus_exchange.consts import DECIMALS
from ducatus_exchange.exchange_requests.views import get_or_create_ducatus_user_and_exchange_request
from ducatus_exchange.payments.api import transfer_with_handle_lottery_and_referral
from ducatus_exchange.quantum.models import Charge
from ducatus_exchange.quantum.serializers import ChargeSerializer
from ducatus_exchange.rates.models import UsdRate


def get_rates():
    usd_prices = {}
    rate = UsdRate.objects.first()

    usd_prices['USD'] = rate.usd_price
    usd_prices['EUR'] = rate.eur_price
    usd_prices['GBP'] = rate.gbp_price
    usd_prices['CHF'] = rate.chf_price
    usd_prices['DUC'] = 0.05

    print('current quantum rates:', usd_prices, flush=True)
    return usd_prices


@swagger_auto_schema(
    method='get',
    responses={"200": ChargeSerializer()},
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
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
            'currency': openapi.Schema(type=openapi.TYPE_STRING),
            'duc_address': openapi.Schema(type=openapi.TYPE_STRING),
            'email': openapi.Schema(type=openapi.TYPE_STRING),
        },
        required=['amount', 'currency', 'duc_address', 'email']
    ),
    responses={"201": openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "charge_id": openapi.Schema(type=openapi.TYPE_NUMBER),
            "redirect_url": openapi.Schema(type=openapi.TYPE_STRING),
        }
    )},
)
@api_view(http_method_names=['POST'])
def add_charge(request: Request):
    # Prepare data
    data = request.data
    duc_address = data.get('duc_address')
    email = data.get('email')
    usd_amount = data.get('amount')
    currency = data.get('currency')
    platform = 'DUC'

    # Calculate amount with rate
    if currency and usd_amount:
        curr_rate = get_rates()[currency]
        amount = round(usd_amount / float(curr_rate), 2)
        data['amount'] = amount

    # raise error if not valid before all logic. Should be 400
    serializer = ChargeSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    user, exchange_request = get_or_create_ducatus_user_and_exchange_request(
        request, duc_address, platform, email
    )

    model = serializer.save()
    model.exchange_request = exchange_request
    model.save()

    answer = {
        "charge_id": model.charge_id,
        "redirect_url": model.redirect_url
    }
    return Response(answer)


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

            print(f'try transfer DUC for charge {charge_id}', flush=True)
            transfer_duc(charge)
    return Response(200)


def transfer_duc(charge):
    # Calc rate and amount
    rates = get_rates()
    duc_rate = rates['DUC']

    value = charge.amount * DECIMALS['DUC'] / DECIMALS[charge.currency]
    sent_amount = int(value / float(duc_rate))

    payment = charge.create_payment(sent_amount, duc_rate)

    transfer_with_handle_lottery_and_referral(payment)

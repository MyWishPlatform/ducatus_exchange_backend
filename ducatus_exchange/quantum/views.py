import logging

from django.db import IntegrityError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from ducatus_exchange.consts import DECIMALS
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.quantum.models import Charge
from ducatus_exchange.quantum.serializers import ChargeSerializer
from ducatus_exchange.rates.models import UsdRate
from ducatus_exchange.payments.api import create_voucher, send_voucher_email


logger = logging.getLogger(__name__)


def get_rates():
    usd_prices = {}
    rate = UsdRate.objects.first()

    usd_prices['USD'] = rate.usd_price
    usd_prices['EUR'] = rate.eur_price
    usd_prices['GBP'] = rate.gbp_price
    usd_prices['CHF'] = rate.chf_price
    usd_prices['DUC'] = rate.duc_price

    logger.info(msg=f'current quantum rates: {usd_prices}')
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
            'email': openapi.Schema(type=openapi.TYPE_STRING),
        },
        required=['amount', 'currency', 'email']
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
    raw_usd_amount = data.get('amount')
    currency = data.get('currency')

    # Calculate amount with rate
    if currency and raw_usd_amount:
        curr_rate = get_rates()[currency]
        usd_amount = raw_usd_amount * DECIMALS[currency]
        amount = round(usd_amount / float(curr_rate))
        data['amount'] = amount

    # raise error if not valid before all logic. Should be 400
    serializer = ChargeSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    model = serializer.save()
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

        charge = Charge.objects.filter(charge_id=charge_id).first()
        if charge and status == 'Withdrawn':
            if Payment.objects.filter(charge_id=charge.id):
                logger.info(msg=f'WARN! Payment for Charge {charge.id}'
                      f' with quantum id {charge.charge_id} already exist. Decline payment')
                return Response(200)

            logger.info(msg=f'try create voucher for charge {charge_id}')
            usd_amount, _ = calculate_amount(charge, 'USD')
            raw_usd_amount = usd_amount / DECIMALS['USD']
            try:
                voucher = create_voucher(raw_usd_amount, charge_id=charge_id)
            except IntegrityError as e:
                if 'voucher code' not in e.args[0]:
                    raise e
                voucher = create_voucher(raw_usd_amount, charge_id=charge_id)

            sent_amount, duc_rate = calculate_amount(charge, 'DUC')
            charge.create_payment(sent_amount, duc_rate)
            send_voucher_email(voucher, charge.email, raw_usd_amount)
            charge.status = status
            charge.save()
    return Response(200)


def calculate_amount(charge, curr):
    rates = get_rates()
    rate = rates.get(curr, None)
    dec = DECIMALS.get(curr, None)
    if not rate and not dec:
        raise KeyError(f'Cant calculate rate with currency {curr}')
    value = charge.amount * dec / DECIMALS[charge.currency]
    usd_amount = int(value / float(rate))
    return usd_amount, rate

from django.core.mail import send_mail
from django.db import IntegrityError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from ducatus_exchange.consts import DECIMALS
from ducatus_exchange.email_messages import voucher_html_body, warning_html_style
from ducatus_exchange.lottery.api import LotteryRegister
from ducatus_exchange.quantum.models import Charge
from ducatus_exchange.quantum.serializers import ChargeSerializer
from ducatus_exchange.rates.models import UsdRate
from ducatus_exchange.settings_local import CONFIRMATION_FROM_EMAIL


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
            print(f'try create voucher for charge {charge_id}', flush=True)
            usd_amount = calculate_usd_amount(charge)
            try:
                voucher = charge.create_voucher(usd_amount)
            except IntegrityError as e:
                if 'voucher code' not in e.args[0]:
                    raise e
                voucher = charge.create_voucher(usd_amount)

            send_voucher_email(voucher, charge.email, usd_amount)
            charge.status = status
            charge.save()
    return Response(200)


def calculate_usd_amount(charge):
    rates = get_rates()
    usd_rate = rates['USD']
    # FIXME do i need to count dec for fiat?
    value = charge.amount * DECIMALS['USD'] / DECIMALS[charge.currency]
    usd_amount = int(value / float(usd_rate))
    return usd_amount


def send_voucher_email(voucher, to_email, usd_amount):
    conn = LotteryRegister.get_mail_connection()

    html_body = voucher_html_body.format(
        voucher_code=voucher['voucher_code']
    )

    send_mail(
        'Your DUC Purchase Confirmation for ${}'.format(round(usd_amount, 2)),
        '',
        CONFIRMATION_FROM_EMAIL,
        [to_email],
        connection=conn,
        html_message=warning_html_style + html_body,
    )
    print('warning message sent successfully to {}'.format(to_email))

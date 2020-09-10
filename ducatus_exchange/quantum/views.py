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
from ducatus_exchange.exchange_requests.views import get_or_create_ducatus_user_and_exchange_request
from ducatus_exchange.lottery.api import LotteryRegister
from ducatus_exchange.payments.models import Payment
from ducatus_exchange.quantum.models import Charge
from ducatus_exchange.quantum.serializers import ChargeSerializer
from ducatus_exchange.rates.models import UsdRate
from ducatus_exchange.settings_local import CONFIRMATION_FROM_EMAIL
from ducatus_exchange.transfers.serializers import DucatusTransferSerializer


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
            if Payment.objects.filter(charge_id=charge.id):
                print('WARN! Payment for Charge {} with quantum id {} already exist. Decline payment'.format(
                    charge.id, charge.charge_id
                ), flush=True)
                return Response(200)

            print(f'try create voucher for charge {charge_id}', flush=True)
            usd_amount, _ = calculate_amount(charge, 'USD')
            raw_usd_amount = usd_amount / DECIMALS['USD']
            try:
                voucher = charge.create_voucher(raw_usd_amount)
            except IntegrityError as e:
                if 'voucher code' not in e.args[0]:
                    raise e
                voucher = charge.create_voucher(raw_usd_amount)

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


def send_voucher_email(voucher, to_email, usd_amount):
    conn = LotteryRegister.get_mail_connection()

    html_body = voucher_html_body.format(
        voucher_code=voucher['activation_code']
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
    charge = Charge.objects.filter(charge_id=charge_id).first()
    transfer_dict = request.data.get('transfer', {})
    duc_address = transfer_dict.get('duc_address')

    # Prepare values for create transfer object
    _, exchange_request = get_or_create_ducatus_user_and_exchange_request(request, duc_address, platform, charge.email)
    payment = Payment.objects.get(charge__charge_id=charge_id)
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

    # Register all prepared values in lottery
    lottery_entrypoint = LotteryRegister(transfer)
    lottery_entrypoint.try_register_to_lotteries()

    return Response(200)

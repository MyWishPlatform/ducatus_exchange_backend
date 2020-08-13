from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

from ducatus_exchange.quantum.models import Charge
from ducatus_exchange.quantum.serializers import ChargeSerializer


@api_view(http_method_names=['GET'])
def get_charge(request: Request, charge_id: int):
    try:
        charge = Charge.objects.get(charge_id=charge_id)
    except Charge.DoesNotExist:
        raise NotFound

    return Response(ChargeSerializer().to_representation(charge))


@api_view(http_method_names=['POST'])
def add_charge(request: Request):
    data = request.data

    serializer = ChargeSerializer(data=data)
    if serializer.is_valid(raise_exception=True):
        serializer.save()

    return Response(serializer.data)


@api_view(http_method_names=['POST'])
def change_status(request: Request):
    if request.data['type'] == 'Charge':
        charge_id = request.data['data']['id']
        if request.data['data']['status'] == 'Withdrawn':
            print(f'try transfer DUC for charge {charge_id}', flush=True)

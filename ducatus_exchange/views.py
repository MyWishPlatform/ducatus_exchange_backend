from django.core.mail import send_mail
from django.core.validators import EmailValidator
from rest_framework.views import APIView
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from ducatus_exchange.settings import FEEDBACK_EMAIL, DEFAULT_FROM_EMAIL


class FeedbackForm(APIView):

    @swagger_auto_schema(
        operation_description="post parameters to send feedback message",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'email', 'phone', 'message'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'tel': openapi.Schema(type=openapi.TYPE_STRING),
                'message': openapi.Schema(type=openapi.TYPE_STRING)
            },
        ),
        # responses={200: {'result': 'ok'}},

    )
    def post(self, request):
        print(request.data)
        name = request.data.get('name')
        email = request.data.get('email')
        phone_number = request.data.get('tel')
        message = request.data.get('message')

        # validate data
        if any([name=='', email=='', phone_number=='', message=='']):
            return Response({'result': 'empty data not allowed'})
        validator = EmailValidator()
        validator(email)
        if not phone_number.isdigit() or len(phone_number) < 10:
            return Response({'result': 'invalid phone number'})

        # send message
        text = """
            Name: {name}
            E-mail: {email}
            Message: {message}
            Phone: {phone}
            """.format(
            name=name, email=email, phone=phone_number, message=message
        )
        send_mail(
            'Request from rocknblock.io contact form',
            text,
            DEFAULT_FROM_EMAIL,
            [FEEDBACK_EMAIL]
        )
        return Response({'result': 'ok'})

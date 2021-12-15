from rest_framework import serializers
from django.core.mail import send_mail
from ducatus_exchange.settings import (
    FEEDBACK_EMAIL,
    DEFAULT_FROM_EMAIL)


class FeedbackFormSerializer(serializers.Serializer):
    email = serializers.EmailField()
    message = serializers.CharField(max_length=500)
    subject = serializers.CharField(max_length=30)

    def send_to_email(self):
        email_body = f"""
            Email: {self.data['email']}
            Message: {self.data['message']}
        """
        send_mail(self.data['subject'], email_body,
                  DEFAULT_FROM_EMAIL, [FEEDBACK_EMAIL])




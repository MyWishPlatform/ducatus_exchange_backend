from django.urls import path, include

from .views import PaymentView


urlpatterns = [
    path('', PaymentView.as_view()),
]
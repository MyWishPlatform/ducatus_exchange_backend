import statistics

from django.conf.urls import url
from django.urls import path

from . import views

app_name = "stats"
# app_name will help us do a reverse look-up latter.
urlpatterns = [
    path('statistics/<int:days>', views.StatsHandler.as_view())


]

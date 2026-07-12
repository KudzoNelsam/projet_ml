from django.urls import path
from . import views

app_name = "predictor"
urlpatterns = [path("", views.prediction_view, name="predict"), path("predict/", views.prediction_view), path("predict/history/", views.history_view, name="history")]

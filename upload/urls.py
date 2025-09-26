# upload/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("", views.upload_form, name="upload_form"),
    path("api/mask/", views.mask_api, name="mask_api"),
]

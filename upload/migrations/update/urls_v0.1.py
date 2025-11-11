# upload/urls.py

'''페이지 요청 발생 시 가장 먼저 호출되는 파일
URL과 views.py 안의 함수를 연결하는 역할'''
"""
from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("", views.upload_form, name="upload_form"),
    path("api/mask/", views.mask_api, name="mask_api"),
    path("convert/ppt_to_pdf/", views.ppt_to_pdf, name="ppt_to_pdf"),
    path("api/mask_ai/", views.mask_ai_api, name="mask_ai_api"),
    path("convert/docx_to_pdf/", views.docx_to_pdf, name="docx_to_pdf"),
]
"""

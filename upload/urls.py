# upload/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # 헬스 체크
    path("health/", views.health, name="health"),

    # 메인 페이지
    path("", views.index_page, name="index"),

    # 페이지 라우팅 (HTML)
    path("ppt/", views.ppt_page, name="ppt_page"),
    path("docx/", views.docx_page, name="docx_page"),
    path("mask/fast/", views.mask_fast_page, name="mask_fast_page"),
    path("mask/ocr/", views.mask_ocr_page, name="mask_ocr_page"),

    # API 엔드포인트
    path("api/mask/", views.mask_api, name="mask_api"),
    path("api/mask_ai/", views.mask_ai_api, name="mask_ai_api"),

    # 파일 변환 엔드포인트
    path("convert/ppt_to_pdf/", views.ppt_to_pdf, name="ppt_to_pdf"),
    path("convert/docx_to_pdf/", views.docx_to_pdf, name="docx_to_pdf"),
]

# upload/urls.py

'''페이지 요청 발생 시 가장 먼저 호출되는 파일
URL과 views.py 안의 함수를 연결하는 역할'''

from django.urls import path
from . import views

# 클라이언트가 접근하는 경로(엔드포인트) : "","health/"... -> views.XXX와 연결되어 XXX함수가 실행됨
urlpatterns = [
    # 서버 상태 확인 (헬스체크용)
    path("health/", views.health, name="health"),

    # 기본 페이지 (파일 업로드 폼)
    path("", views.upload_form, name="upload_form"),

    # 일반 텍스트 기반 PDF 마스킹 (Kiwi 기반)
    path("api/mask/", views.mask_api, name="mask_api"),

    # PPT → PDF 변환 엔드포인트
    path("convert/ppt_to_pdf/", views.ppt_to_pdf, name="ppt_to_pdf"),

    # AI 기반 OCR 마스킹 (PaddleOCR 사용)
    path("api/mask_ai/", views.mask_ai_api, name="mask_ai_api"),

    # DOCX → PDF 변환 엔드포인트
    path("convert/docx_to_pdf/", views.docx_to_pdf, name="docx_to_pdf"),
]

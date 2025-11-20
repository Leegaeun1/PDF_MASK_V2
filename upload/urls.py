from django.urls import path
from . import views

urlpatterns = [
    # 헬스 체크
    path("health/", views.health, name="health"),

    # 메인 페이지 및 라우팅 
    path("", views.index_page, name="index"),
    path("ppt/", views.ppt_page, name="ppt_page"),
    path("docx/", views.docx_page, name="docx_page"),
    path("mask/fast/", views.mask_fast_page, name="mask_fast_page"),
    path("mask/ocr/", views.mask_ocr_page, name="mask_ocr_page"),

    # 1. 기존 API 엔드포인트: 이제 Task 위임 역할만 합니다.
    path("api/mask/", views.mask_api, name="mask_api"),
    path("api/mask_ai/", views.mask_ai_api, name="mask_ai_api"),

    # 2. 파일 변환 엔드포인트: 이제 Task 위임 역할만 합니다.
    path("convert/ppt_to_pdf/", views.ppt_to_pdf, name="ppt_to_pdf"),
    path("convert/docx_to_pdf/", views.docx_to_pdf, name="docx_to_pdf"),

    # 3. 새로운 Polling API: 작업 상태 확인
    path("api/status/<uuid:job_id>/", views.get_job_status, name="get_job_status"),
    
    # 4. 새로운 Download API: 결과 다운로드
    path("api/download/<uuid:job_id>/", views.download_result, name="download_result"),
]
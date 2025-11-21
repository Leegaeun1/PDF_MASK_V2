from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import os
import logging
import uuid
import shutil
import tempfile
from celery.result import AsyncResult # Celery 작업 상태 확인용
from django.utils.encoding import escape_uri_path # 한글 파일명 처리용 


from .tasks import (
    exec_ppt_to_pdf_task, 
    exec_docx_to_pdf_task, 
    exec_mask_fast_task, 
    exec_mask_ai_ocr_task
)
logger = logging.getLogger(__name__)

CELERY_JOB_DIR = "/tmp/celery_jobs"

# =============================
# Helper: 파일 처리 및 Job ID 생성
# =============================

def save_uploaded_file_and_get_path(uploaded_file, job_id):
    """
    업로드된 파일을 임시 작업 디렉토리에 저장하고 경로를 반환합니다.
    중요: 파일명을 job_id로 변경하여 특수문자/공백 문제를 원천 차단합니다.
    """
    # 1. 작업 디렉토리 생성
    job_workdir = os.path.join(CELERY_JOB_DIR, job_id)
    os.makedirs(job_workdir, exist_ok=True)
    
    # 2. 확장자 추출 (예: .pptx)
    ext = os.path.splitext(uploaded_file.name)[1]
    
    # 3. 안전한 파일명 생성 (예: a1b2-c3d4.pptx)
    safe_filename = f"{job_id}{ext}"
    
    # 4. 저장 경로 결합
    in_path = os.path.join(job_workdir, safe_filename)
    
    # 5. 파일 저장
    with open(in_path, "wb") as out:
        for chunk in uploaded_file.chunks():
            out.write(chunk)
            
    return in_path


def generate_unique_id():
    """작업의 고유 ID를 생성합니다."""
    return str(uuid.uuid4())

# =============================
#          Health Check (유지)
# =============================

def health(request):
    return JsonResponse({"status": "ok"})


# =============================
#      Page Rendering Views (유지)
# =============================

def index_page(request):
    return render(request, "upload/index.html")

def ppt_page(request):
    return render(request, "upload/ppt.html")

def docx_page(request):
    return render(request, "upload/docx.html")

def mask_fast_page(request):
    return render(request, "upload/mask_fast.html")

def mask_ocr_page(request):
    return render(request, "upload/mask_ocr.html")


# =============================
#        PPT → PDF 
# =============================
# 이 함수는 연산을 수행하지 않고, Task를 위임하고 즉시 응답합니다.
def ppt_to_pdf(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    f = request.FILES.get("file")
    if not f:
        return HttpResponseBadRequest("No file")

    # 1. 고유 ID 생성
    job_id = generate_unique_id()
    
    # 2. 파일 저장 (빠른 I/O만 수행)
    try:
        in_path = save_uploaded_file_and_get_path(f, job_id)
    except Exception as e:
        return JsonResponse({"error": f"File save failed: {e}"}, status=500)

    try:
        # 3. Celery Task 위임
        # 무거운 연산은 Worker에게 맡기고 바로 반환합니다.
        task_result = exec_ppt_to_pdf_task.apply_async(args=[job_id, in_path, f.name], task_id=job_id)# type: ignore
        logger.info(f"PPT to PDF job submitted: {job_id}, Celery ID: {task_result.id}")

        # 4. 즉시 응답 (사용자 대기 시간 없음)
        return JsonResponse({
            "status": "Job accepted and processing",
            "job_id": job_id,
            "task_id": task_result.id,
            "check_url": f"/api/status/{job_id}" # 상태 확인 API 경로 안내
        }, status=202) # 202 Accepted 코드는 비동기 작업 접수 시 표준 응답입니다.
    except Exception as e:
        # 이 블록에서 Redis 연결 실패(ConnectionRefused)를 포함한 모든 Traceback을 강제 출력합니다.
        logger.exception("CRITICAL EXCEPTION: Failed to submit job to Celery queue.")
        # 사용자에게는 500 오류를 반환합니다.
        return JsonResponse({"error": "Failed to submit job to queue. Check Redis/Celery connection."}, status=500)


# =============================
#       DOCX → PDF 
# =============================
# **이 함수 역시 Task를 위임하고 즉시 응답합니다.**
def docx_to_pdf(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    f = request.FILES.get("file")
    if not f:
        return HttpResponseBadRequest("No file")

    job_id = generate_unique_id()
    
    try:
        in_path = save_uploaded_file_and_get_path(f, job_id)
    except Exception as e:
        return JsonResponse({"error": f"File save failed: {e}"}, status=500)

    # Celery Task 위임
    try:
        task_result = exec_docx_to_pdf_task.apply_async(args=[job_id, in_path, f.name], task_id=job_id)# type: ignore
        logger.info(f"DOCX to PDF job submitted: {job_id}, Celery ID: {task_result.id}")

        # 즉시 응답
        return JsonResponse({
            "status": "Job accepted and processing",
            "job_id": job_id,
            "task_id": task_result.id,
            "check_url": f"/api/status/{job_id}"
        }, status=202)
    except Exception as e:
        # 이 블록에서 Redis 연결 실패(ConnectionRefused)를 포함한 모든 Traceback을 강제 출력합니다.
        logger.exception("CRITICAL EXCEPTION: Failed to submit job to Celery queue.")
        # 사용자에게는 500 오류를 반환합니다.
        return JsonResponse({"error": "Failed to submit job to queue. Check Redis/Celery connection."}, status=500)


# =============================
#         Fast Mask API
# =============================
@csrf_exempt
@require_http_methods(["POST"])
def mask_api(request):
    f = request.FILES.get("file")
    if not f:
        return HttpResponseBadRequest("file field is required (PDF)")

    def _get(name, default=None):
        return request.POST.get(name, request.GET.get(name, default))

    opts = {}
    if _get("mode"): opts["mode"] = _get("mode")
    if _get("target_mode"): opts["target_mode"] = _get("target_mode")
    if _get("mask_ratio"):
        try:
            opts["mask_ratio"] = float(_get("mask_ratio"))
        except ValueError:
             return HttpResponseBadRequest("Invalid mask_ratio format")

    job_id = generate_unique_id()
    try:
        in_path = save_uploaded_file_and_get_path(f, job_id)
    except Exception as e:
        return JsonResponse({"error": f"File save failed: {e}"}, status=500)

    try:
        # Celery Task 위임
        task_result = exec_mask_fast_task.apply_async(args=[job_id, in_path,opts, f.name], task_id=job_id)# type: ignore
        logger.info(f"Fast Mask job submitted: {job_id}, Celery ID: {task_result.id}")

        # 즉시 응답
        return JsonResponse({
            "status": "Job accepted and processing",
            "job_id": job_id,
            "task_id": task_result.id,
            "check_url": f"/api/status/{job_id}"
        }, status=202)
    except Exception as e:
        # 이 블록에서 Redis 연결 실패(ConnectionRefused)를 포함한 모든 Traceback을 강제 출력합니다.
        logger.exception("CRITICAL EXCEPTION: Failed to submit job to Celery queue.")
        # 사용자에게는 500 오류를 반환합니다.
        return JsonResponse({"error": "Failed to submit job to queue. Check Redis/Celery connection."}, status=500)

# =============================
#         AI OCR Mask API 
# =============================
@csrf_exempt
def mask_ai_api(request):
    if request.method != "POST" or not request.FILES.get("file"):
        return HttpResponseBadRequest("POST method and file upload required")

    f = request.FILES["file"]
    
    job_id = generate_unique_id()
    try:
        in_path = save_uploaded_file_and_get_path(f, job_id)
    except Exception as e:
        return JsonResponse({"error": f"File save failed: {e}"}, status=500)

    try:
    # Celery Task 위임
        task_result = exec_mask_ai_ocr_task.apply_async(args=[job_id, in_path, f.name], task_id=job_id)# type: ignore
        logger.info(f"AI OCR Mask job submitted: {job_id}, Celery ID: {task_result.id}")

        # 즉시 응답
        return JsonResponse({
            "status": "Job accepted and processing",
            "job_id": job_id,
            "task_id": task_result.id,
            "check_url": f"/api/status/{job_id}"
        }, status=202)
    except Exception as e:
        # 이 블록에서 Redis 연결 실패(ConnectionRefused)를 포함한 모든 Traceback을 강제 출력합니다.
        logger.exception("CRITICAL EXCEPTION: Failed to submit job to Celery queue.")
        # 사용자에게는 500 오류를 반환합니다.
        return JsonResponse({"error": "Failed to submit job to queue. Check Redis/Celery connection."}, status=500)


# ===============================================
#         NEW: Task Status API
# ===============================================

@require_http_methods(["GET"])
def get_job_status(request, job_id):
    """
    클라이언트가 작업 상태를 주기적으로 확인하는 API (Polling)
    """
    job_id = str(job_id)
    # Celery ID를 사용하여 Task 상태 조회
    task = AsyncResult(job_id)

    status_map = {
        'PENDING': 'Processing',    # 작업이 큐에 있거나 시작 대기 중
        'STARTED': 'Processing',    # 작업 시작됨
        'SUCCESS': 'Completed',     # 작업 성공
        'FAILURE': 'Failed',      # 작업 실패
        'RETRY': 'Processing',      # 재시도 중
    }
    
    current_status = status_map.get(task.status, 'Unknown')
    
    response_data = {
        "job_id": job_id,
        "status": current_status,
        "task_status": task.status # Celery의 상세 상태
    }

    if task.status == 'SUCCESS':
        # 작업이 성공하면, Celery의 결과(result)에서 파일 경로를 가져옵니다.
        file_path = task.result 
        
        # 실제 환경에서는 DB에서 output_path를 가져옵니다.
        if file_path:
            response_data['download_url'] = f"/api/download/{job_id}"
        else:
            response_data['status'] = 'Error'
            response_data['message'] = 'Task succeeded but result path is missing.'

    elif task.status == 'FAILURE':
        response_data['message'] = str(task.result) # 실패 메시지
        
    return JsonResponse(response_data)


# ================================================
#         NEW: Result Download API
# ================================================

@require_http_methods(["GET"])
# download_result 함수 전체 수정
def download_result(request, job_id):
    job_id = str(job_id)
    task = AsyncResult(job_id)
    
    if task.status != 'SUCCESS':
        return JsonResponse({"error": "Job is not completed yet"}, status=400)
    
    result_data = task.result 
    
    # 예전 버전 호환성을 위해 dict인지 확인
    if isinstance(result_data, dict):
        result_path = result_data['path']
        original_name = result_data['filename']
    else:
        result_path = result_data
        original_name = "converted.pdf" # 비상용 이름

    if not result_path or not os.path.exists(result_path):
        return JsonResponse({"error": "File not found"}, status=404)

    try:
        with open(result_path, "rb") as f:
            file_data = f.read()

        # 서버 청소
        job_dir = os.path.dirname(result_path)
        shutil.rmtree(job_dir, ignore_errors=True)
        
        # 한글 파일명 깨짐 방지 처리
        encoded_filename = escape_uri_path(original_name)
        
        response = HttpResponse(file_data, content_type='application/pdf')
        # 파일명을 여기서 설정해줍니다.
        response['Content-Disposition'] = f'attachment; filename="{encoded_filename}"'
        return response

    except Exception as e:
        logger.error(f"Download error: {e}")
        return JsonResponse({"error": "Server error"}, status=500)
import os
import shutil
import subprocess
import logging
from celery import shared_task
from celery.result import AsyncResult # AsyncResult 임포트 (Helper 함수에 필요)

# 기존 views.py에서 사용하던 모듈 임포트
from engine.mask_engine import mask_pdf_bytes
from engine.ai_mask_engine import mask_pdf_bytes_ai

# Job Status를 추적하기 위해 Celery 인스턴스에 접근합니다.
from pdfuploader.celery import app

logger = logging.getLogger(__name__)

# 임시 저장소 경로 (Docker/Cloud Run 환경의 /tmp를 활용)
CELERY_JOB_DIR = "/tmp/celery_jobs"

# =======================================================
# File I/O & Status Helpers
# =======================================================

def exec_update_job_status(job_id, status, result_path=None):
    """Celery Task 상태를 DB/Redis에 업데이트하는 함수입니다."""
    task = app.AsyncResult(job_id)
    # 실제 DB 업데이트 로직은 여기에 들어갑니다.
    logger.info(f"Job {job_id} status updated to: {status}")

def exec_get_job_file_path(job_id, filename):
    """작업 디렉토리를 생성하고 파일 경로를 반환합니다."""
    job_workdir = os.path.join(CELERY_JOB_DIR, job_id)
    os.makedirs(job_workdir, exist_ok=True)
    return os.path.join(job_workdir, filename)

# =======================================================
# 1. PPT -> PDF 비동기 변환 Task
# =======================================================

@shared_task(bind=True, name="ppt_to_pdf_task")
def exec_ppt_to_pdf_task(self, job_id, in_path):
    exec_update_job_status(job_id, 'PROCESSING')
    workdir = os.path.dirname(in_path)
    
    try:
        env = os.environ.copy()
        env["HOME"] = "/tmp"

        # 🚨 LibreOffice 안정화: 사용자 프로필을 임시 디렉토리에 강제 지정 (충돌 방지)
        # 💡 리스트 형태의 cmd를 유지하여 쉘 인젝션 위험을 낮춤
        cmd = [
            "soffice",
            "--headless", "--invisible", "--nodefault", "--nocrashreport",
            "--nolockcheck", "--nologo",
            # 💡 사용자 프로필을 /tmp/libreoffice_profile로 강제 지정하여 Worker 간 충돌 방지
            f"-env:UserInstallation=file:///tmp/libreoffice_profile/{job_id}",
            "--convert-to", "pdf:impress_pdf_Export",
            "--outdir", workdir,
            in_path, 
        ]
        
        # 💡 subprocess.run 호출 강화: stdout/stderr 캡쳐 유지
        completed = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=180, env=env 
        )
        
        # 🚨 리턴 코드 != 0 검사 (LibreOffice가 오류 코드를 반환했을 때)
        if completed.returncode != 0:
            raise Exception(f"LibreOffice failed rc={completed.returncode}. STDOUT: {completed.stdout.decode(errors='ignore')}. STDERR: {completed.stderr.decode(errors='ignore')}")

        pdf_name = os.path.splitext(os.path.basename(in_path))[0] + ".pdf"
        pdf_path = os.path.join(workdir, pdf_name)
        
        # 🚨 파일 존재 여부 최종 확인 (LibreOffice가 성공했다고 거짓말 했을 때)
        if not os.path.exists(pdf_path):
            # LibreOffice가 0을 반환했지만 파일이 없는 경우, 상세 로그를 출력합니다.
            raise Exception(f"PDF file not produced. LibreOffice returned 0. Stdout: {completed.stdout.decode(errors='ignore')}. Stderr: {completed.stderr.decode(errors='ignore')}")

        exec_update_job_status(job_id, 'COMPLETED', result_path=pdf_path)
        return pdf_path

    except Exception as e:
        logger.error(f"PPT to PDF Task Failed for {job_id}: {e}")
        exec_update_job_status(job_id, 'FAILED')
        return None
    finally:
        # 작업 완료 후 LibreOffice 프로필 폴더 삭제 (Worker 환경 정리)
        shutil.rmtree(f"/tmp/libreoffice_profile/{job_id}", ignore_errors=True)

# =======================================================
# 2. DOCX -> PDF 비동기 변환 Task (수정 적용)
# =======================================================

@shared_task(bind=True, name="docx_to_pdf_task")
def exec_docx_to_pdf_task(self, job_id, in_path):
    exec_update_job_status(job_id, 'PROCESSING')
    workdir = os.path.dirname(in_path)
    
    try:
        env = os.environ.copy()
        env["HOME"] = "/tmp"

        cmd = [
            "soffice",
            "--headless", "--invisible", "--nodefault", "--nocrashreport",
            "--nolockcheck", "--nologo",
            f"-env:UserInstallation=file:///tmp/libreoffice_profile/{job_id}", # 💡 프로필 강제 지정
            "--convert-to", "pdf:writer_pdf_Export",
            "--outdir", workdir,
            in_path,
        ]

        completed = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=180, env=env 
        )
        
        if completed.returncode != 0:
            raise Exception(f"LibreOffice failed rc={completed.returncode}. STDOUT: {completed.stdout.decode(errors='ignore')}. STDERR: {completed.stderr.decode(errors='ignore')}")

        pdf_name = os.path.splitext(os.path.basename(in_path))[0] + ".pdf"
        pdf_path = os.path.join(workdir, pdf_name)
        
        if not os.path.exists(pdf_path):
             raise Exception(f"PDF file not produced. LibreOffice returned 0. Stdout: {completed.stdout.decode(errors='ignore')}. Stderr: {completed.stderr.decode(errors='ignore')}")
            
        exec_update_job_status(job_id, 'COMPLETED', result_path=pdf_path)
        return pdf_path

    except Exception as e:
        logger.error(f"DOCX to PDF Task Failed for {job_id}: {e}")
        exec_update_job_status(job_id, 'FAILED')
        return None
    finally:
        shutil.rmtree(f"/tmp/libreoffice_profile/{job_id}", ignore_errors=True)


# =======================================================
# 3. Fast Mask 비동기 Task (유지)
# ...
# =======================================================

@shared_task(bind=True, name="mask_fast_task")
def exec_mask_fast_task(self, job_id, in_path, opts):
    exec_update_job_status(job_id, 'PROCESSING')
    
    try:
        if not os.path.exists(in_path):
             # 🚨 파일 존재 여부 최종 확인
             raise FileNotFoundError(f"Input file not found at {in_path}. Check Web Worker save path.")
             
        with open(in_path, 'rb') as f:
            pdf_bytes = f.read()
        
        out_bytes = mask_pdf_bytes(pdf_bytes, **opts)
        
        result_filename = f"{job_id}_fast_masked.pdf"
        out_path = exec_get_job_file_path(job_id, result_filename)
        with open(out_path, 'wb') as out_f:
            out_f.write(out_bytes)

        exec_update_job_status(job_id, 'COMPLETED', result_path=out_path)
        return out_path
        
    except Exception as e:
        logger.error(f"Fast Mask Task Failed for {job_id}: {e}")
        exec_update_job_status(job_id, 'FAILED')
        return None

# =======================================================
# 4. AI OCR Mask 비동기 Task (유지)
# ...
# =======================================================

@shared_task(bind=True, name="mask_ai_ocr_task")
def exec_mask_ai_ocr_task(self, job_id, in_path):
    exec_update_job_status(job_id, 'PROCESSING')
    
    try:
        if not os.path.exists(in_path):
             raise FileNotFoundError(f"Input file not found at {in_path}. Check Web Worker save path.")
             
        with open(in_path, 'rb') as f:
            pdf_bytes = f.read()

        masked_pdf = mask_pdf_bytes_ai(pdf_bytes)
        
        result_filename = f"{job_id}_ai_masked.pdf"
        out_path = exec_get_job_file_path(job_id, result_filename)
        with open(out_path, 'wb') as out_f:
            out_f.write(masked_pdf)

        exec_update_job_status(job_id, 'COMPLETED', result_path=out_path)
        return out_path
        
    except Exception as e:
        logger.error(f"AI OCR Mask Task Failed for {job_id}: {e}")
        exec_update_job_status(job_id, 'FAILED')
        return None
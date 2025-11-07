# upload/views.py

'''앱의 기능 구현'''

from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest,FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import os
import sys
import tempfile
import subprocess
import logging, os, shutil, subprocess, tempfile


from engine.mask_engine import mask_pdf_bytes


def health(request):
    """간단한 헬스 체크. 서버가 정상적으로 작동하는지 확인"""
    return JsonResponse({"status": "ok"})

logger = logging.getLogger(__name__)

def ppt_to_pdf(request):
    if request.method != "POST": # 파일 업로드와 같은 데이터만 처리해야하므로 post가 아니면 400 오류 반환!
        return HttpResponseBadRequest("POST only")

    f = request.FILES.get("file")
    if not f: # 파일 없으면 400오류
        return HttpResponseBadRequest("No file")

    # LibreOffice가 사용자 홈에 뭔가 쓰려고 해서, 컨테이너에선 HOME을 /tmp로 고정하는게 안전
    env = os.environ.copy()
    env["HOME"] = "/tmp" # 쓰기 가능한 임시 경로로 설정

    # 각 요청마다 /tmp에 격리된 작업 디렉터리 생성. 여러 사용자의 요청이 동시에 처리될때 파일 충돌 방지! /tmp/ppt2pdf_~~~로 폴더가 생성된다
    workdir = tempfile.mkdtemp(prefix="ppt2pdf_", dir="/tmp")


    try:
        in_path = os.path.join(workdir, f.name) # 파일의 내용을 작업 디렉토리에 원래 파일 이름으로 저장함
        with open(in_path, "wb") as out:
            for chunk in f.chunks(): # 대용량 파일을 작은 조각으로 나누어 디스크에 기록함!
                out.write(chunk)


        # soffice 경로는 대개 /usr/bin/libreoffice 또는 /usr/bin/soffice
        # 어느 쪽이든 'soffice' 실행 가능하면 됨
        cmd = [
            "soffice", # LibreOffice 실행하는 명령어
            "--headless", "--invisible", "--nodefault", "--nocrashreport", 
            "--nolockcheck", "--nologo", # GUI없이 백그라운드에서 실행하기 위해 필요!
            "--convert-to", "pdf:impress_pdf_Export", # pdf(출력 파일 형식) : impress_pdf_Export(ppt/pttx문서를 pdf로 변환할때 사용하는 LibreOffice의 특정 필터 이름)
            "--outdir", workdir,# 변환된 pdf파일을 저장할 디렉터리
            in_path, # 변환할 원본 ppt 파일의 경로
        ]

        # 변환 작업이 30초 초과하면 자동으로 중단하고 예외 발생. 
        completed = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=30, env=env
        )

        if completed.returncode != 0: # LibreOffice 실행이 실패했을때. 시스템오류 또는 파일 손생
            logger.error("LibreOffice failed rc=%s\nstdout=%s\nstderr=%s", # 오류 코드 출력
                         completed.returncode,
                         completed.stdout.decode(errors="ignore"),
                         completed.stderr.decode(errors="ignore"))
            return JsonResponse( # 500오류 발생 + 실패 정보를 JSON형식으로 반환
                {"error": "libreoffice-failed",
                 "stderr": completed.stderr.decode(errors="ignore")},
                status=500
            )


        pdf_name = os.path.splitext(os.path.basename(in_path))[0] + ".pdf" # 입력 파일이름.pdf으로 이름 바꿈 
        pdf_path = os.path.join(workdir, pdf_name) # 출력파일 경로를 만듬
        if not os.path.exists(pdf_path): # pdf파일이 실제로 생성되었는지 확인. 존재하지 않으면 500오류 반환
            logger.error("PDF not produced. stdout=%s stderr=%s",
                         completed.stdout.decode(errors="ignore"),
                         completed.stderr.decode(errors="ignore"))
            return JsonResponse({"error": "pdf-not-produced"}, status=500)

        # 스트리밍 방식으로 응답. 바이너리 읽기 모드로 열어 전달. 주로 다운로드나 첨부한 파일을 받아 처리할때 사용
        # as_attachment = True는 브라우저에서 다운로드 되도록 지정, 이름을 pdf_name으로
        resp = FileResponse(open(pdf_path, "rb"), as_attachment=True, filename=pdf_name)
        return resp

    except subprocess.TimeoutExpired as e: # 실행이 30초 타임아웃 초과했을때. 504 오류
        logger.error("Timeout: %s", e)
        # 여기서 504로 돌려 LB/도메인별 차이를 확인해도 좋음
        return JsonResponse({"error": "timeout", "detail": "conversion took too long"}, status=504)
    except Exception as e: # 위에서 처리되지 않은 모든 예상치 못한 오류 처리
        logger.exception("ppt_to_pdf fatal")
        return JsonResponse({"error": "internal", "detail": str(e)}, status=500)
    finally:
        # 변환 끝나면 작업폴더 삭제
        shutil.rmtree(workdir, ignore_errors=True)

def docx_to_pdf(request):
    """
    DOCX 파일을 PDF로 변환하는 기능 (새로 추가됨)
    """
    if request.method != "POST": # 파일 업로드와 같은 데이터만 처리해야하므로 post가 아니면 400 오류 반환!
        return HttpResponseBadRequest("POST only")

    f = request.FILES.get("file")
    if not f: # 파일 없으면 400오류
        return HttpResponseBadRequest("No file")

    # LibreOffice가 사용자 홈에 뭔가 쓰려고 해서, 컨테이너에선 HOME을 /tmp로 고정하는게 안전
    env = os.environ.copy()
    env["HOME"] = "/tmp" # 쓰기 가능한 임시 경로로 설정

    # 각 요청마다 /tmp에 격리된 작업 디렉터리 생성. 여러 사용자의 요청이 동시에 처리될때 파일 충돌 방지! /tmp/docx2pdf_~~~로 폴더가 생성된다
    workdir = tempfile.mkdtemp(prefix="docx2pdf_", dir="/tmp")


    try:
        in_path = os.path.join(workdir, f.name) # 파일의 내용을 작업 디렉토리에 원래 파일 이름으로 저장함
        with open(in_path, "wb") as out:
            for chunk in f.chunks(): # 대용량 파일을 작은 조각으로 나누어 디스크에 기록함!
                out.write(chunk)


        # soffice 경로는 대개 /usr/bin/libreoffice 또는 /usr/bin/soffice
        # 어느 쪽이든 'soffice' 실행 가능하면 됨
        cmd = [
            "soffice", # LibreOffice 실행하는 명령어
            "--headless", "--invisible", "--nodefault", "--nocrashreport", 
            "--nolockcheck", "--nologo", # GUI없이 백그라운드에서 실행하기 위해 필요!
            # DOCX는 Writer 문서이므로 'writer_pdf_Export' 필터를 사용해야 함
            "--convert-to", "pdf:writer_pdf_Export", 
            "--outdir", workdir,# 변환된 pdf파일을 저장할 디렉터리
            in_path, # 변환할 원본 docx 파일의 경로
        ]

        # 변환 작업이 30초 초과하면 자동으로 중단하고 예외 발생. 
        completed = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=30, env=env
        )

        if completed.returncode != 0: # LibreOffice 실행이 실패했을때. 시스템오류 또는 파일 손생
            logger.error("LibreOffice failed rc=%s\nstdout=%s\nstderr=%s", # 오류 코드 출력
                         completed.returncode,
                         completed.stdout.decode(errors="ignore"),
                         completed.stderr.decode(errors="ignore"))
            return JsonResponse( # 500오류 발생 + 실패 정보를 JSON형식으로 반환
                {"error": "libreoffice-failed",
                 "stderr": completed.stderr.decode(errors="ignore")},
                status=500
            )


        pdf_name = os.path.splitext(os.path.basename(in_path))[0] + ".pdf" # 입력 파일이름.pdf으로 이름 바꿈 
        pdf_path = os.path.join(workdir, pdf_name) # 출력파일 경로를 만듬
        if not os.path.exists(pdf_path): # pdf파일이 실제로 생성되었는지 확인. 존재하지 않으면 500오류 반환
            logger.error("PDF not produced. stdout=%s stderr=%s",
                         completed.stdout.decode(errors="ignore"),
                         completed.stderr.decode(errors="ignore"))
            return JsonResponse({"error": "pdf-not-produced"}, status=500)

        # 스트리밍 방식으로 응답. 바이너리 읽기 모드로 열어 전달. 주로 다운로드나 첨부한 파일을 받아 처리할때 사용
        # as_attachment = True는 브라우저에서 다운로드 되도록 지정, 이름을 pdf_name으로
        resp = FileResponse(open(pdf_path, "rb"), as_attachment=True, filename=pdf_name)
        return resp

    except subprocess.TimeoutExpired as e: # 실행이 30초 타임아웃 초과했을때. 504 오류
        logger.error("Timeout: %s", e)
        # 여기서 504로 돌려 LB/도메인별 차이를 확인해도 좋음
        return JsonResponse({"error": "timeout", "detail": "conversion took too long"}, status=504)
    except Exception as e: # 위에서 처리되지 않은 모든 예상치 못한 오류 처리
        logger.exception("docx_to_pdf fatal")
        return JsonResponse({"error": "internal", "detail": str(e)}, status=500)
    finally:
        # 변환 끝나면 작업폴더 삭제
        shutil.rmtree(workdir, ignore_errors=True)



@require_http_methods(["GET", "POST"])
def upload_form(request):
    """
    GET  : 업로드 폼 템플릿 렌더링
    POST : 업로드된 PDF를 옵션과 함께 마스킹하여 masked.pdf 반환
    """
    if request.method == "GET":
        # 보여줄 html파일 경로
        return render(request, "upload/upload.html")
    
    # POST
    f = request.FILES.get("file")
    if not f:
        return HttpResponseBadRequest("파일이 필요합니다 (field name: file)")

    # POST 우선, 없으면 GET에서 name이라는 이름의 문서 찾기.여기도 없으면 기본값 사용
    def _get(name, default=None):
        return request.POST.get(name, request.GET.get(name, default))

    opts = {}

    # mode: redact | highlight
    m = _get("mode", "redact")
    if m:
        opts["mode"] = m

    # target_mode: both | josa_only | nouns_only
    t = _get("target_mode", "both")
    if t:
        opts["target_mode"] = t

    # mask_ratio: float(0~1)
    r = _get("mask_ratio", "0.95")
    try:
        opts["mask_ratio"] = float(r)
    except ValueError:
        return HttpResponseBadRequest("mask_ratio must be float")

    # 선택 옵션: 최소 마스킹 길이
    ml = _get("min_mask_len")
    if ml is not None and ml != "":
        try:
            opts["min_mask_len"] = int(ml)
        except ValueError:
            return HttpResponseBadRequest("min_mask_len must be int")

    # 선택 옵션: 명사 span 허용 여부 (true/false, 1/0, yes/no, on/off)
    ans = _get("allow_noun_span")
    if ans is not None and ans != "":
        opts["allow_noun_span"] = str(ans).lower() in ("1", "true", "yes", "on")

    # 처리
    try:
        out_bytes = mask_pdf_bytes(f.read(), **opts)
    except Exception as e:
        return HttpResponseBadRequest(f"처리 오류: {e}")
		# 원본 파일 이름 가져오기
    original_filename = f.name
    
    # 파일 이름과 확장자 분리
    name_part, extension = os.path.splitext(original_filename)
    
    # 새로운 파일 이름 만들기
    new_filename = f"{name_part}_masked"
	  # 다운로드 응답
    resp = HttpResponse(out_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{new_filename}.pdf"'
    
    resp["X-Content-Type-Options"] = "nosniff"
    return resp


@csrf_exempt
@require_http_methods(["POST"])
def mask_api(request):
    """
    API 엔드포인트 (multipart/form-data)
    """
    f = request.FILES.get("file")
    if not f:
        return HttpResponseBadRequest("file field is required (PDF)")

    def _get(name, default=None):
        return request.POST.get(name, request.GET.get(name, default))

    opts = {}

    m = _get("mode")
    if m:
        opts["mode"] = m

    t = _get("target_mode")
    if t:
        opts["target_mode"] = t

    r = _get("mask_ratio")
    if r is not None and r != "":
        try:
            opts["mask_ratio"] = float(r)
        except ValueError:
            return HttpResponseBadRequest("mask_ratio must be float")

    ml = _get("min_mask_len")
    if ml is not None and ml != "":
        try:
            opts["min_mask_len"] = int(ml)
        except ValueError:
            return HttpResponseBadRequest("min_mask_len must be int")

    ans = _get("allow_noun_span")
    if ans is not None and ans != "":
        opts["allow_noun_span"] = str(ans).lower() in ("1", "true", "yes", "on")

    try:
        out_bytes = mask_pdf_bytes(f.read(), **opts)
    except Exception as e:
        return HttpResponseBadRequest(f"processing error: {e}")
    
    original_filename = f.name
    name_part, extension = os.path.splitext(original_filename)
    new_filename = f"{name_part}_masked"
    
    resp = HttpResponse(out_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{new_filename}.pdf"'
    resp["X-Content-Type-Options"] = "nosniff"
    return resp

# =============================
#          OCR Logic
# =============================

from engine.ai_mask_engine import mask_pdf_bytes_ai  # 추가
from engine.mask_engine import mask_pdf_bytes        # 기존 엔진 (비교용)

@csrf_exempt
def mask_ai_api(request):
    """
    PaddleOCR 기반 AI 마스킹 API
    """
    if request.method == "POST" and request.FILES.get("file"):
        try:
            uploaded_file = request.FILES["file"]
            pdf_bytes = uploaded_file.read()

            # OCR 기반 마스킹 실행
            masked_pdf = mask_pdf_bytes_ai(pdf_bytes)

            response = HttpResponse(masked_pdf, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="masked_ai.pdf"'
            return response

        except Exception as e:
            print(f"[ERROR] mask_ai_api failed: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "No file uploaded"}, status=400)
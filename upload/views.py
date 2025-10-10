# upload/views.py

'''앱의 기능 구현'''

from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import os

from engine.mask_engine import mask_pdf_bytes


def health(request):
    """간단한 헬스 체크. 서버가 정상적으로 작동하는지 확인"""
    return JsonResponse({"status": "ok"})


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
    new_filename = f"{name_part}_masked{extension}"
	  # 다운로드 응답
    resp = HttpResponse(out_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{new_filename}.pdf"'
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
    new_filename = f"{name_part}_masked{extension}"
    
    resp = HttpResponse(out_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{new_filename}.pdf"'
    return resp

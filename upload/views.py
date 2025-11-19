# /upload/views.py

from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
import os, sys, tempfile, subprocess, logging, shutil

from engine.mask_engine import mask_pdf_bytes
from engine.ai_mask_engine import mask_pdf_bytes_ai

logger = logging.getLogger(__name__)

# =============================
#          Health Check
# =============================

def health(request):
    return JsonResponse({"status": "ok"})


# =============================
#      Page Rendering Views
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
#        PPT → PDF
# =============================

def ppt_to_pdf(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    f = request.FILES.get("file")
    if not f:
        return HttpResponseBadRequest("No file")

    env = os.environ.copy()
    env["HOME"] = "/tmp"

    workdir = tempfile.mkdtemp(prefix="ppt2pdf_", dir="/tmp")

    try:
        in_path = os.path.join(workdir, f.name)
        with open(in_path, "wb") as out:
            for chunk in f.chunks():
                out.write(chunk)

        cmd = [
            "soffice",
            "--headless", "--invisible", "--nodefault", "--nocrashreport",
            "--nolockcheck", "--nologo",
            "--convert-to", "pdf:impress_pdf_Export",
            "--outdir", workdir,
            in_path,
        ]

        completed = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=30, env=env
        )

        if completed.returncode != 0:
            logger.error("LibreOffice failed rc=%s\nstderr=%s",
                         completed.returncode,
                         completed.stderr.decode(errors="ignore"))
            return JsonResponse({"error": "libreoffice-failed"}, status=500)

        pdf_name = os.path.splitext(os.path.basename(in_path))[0] + ".pdf"
        pdf_path = os.path.join(workdir, pdf_name)

        if not os.path.exists(pdf_path):
            logger.error("PDF not produced.")
            return JsonResponse({"error": "pdf-not-produced"}, status=500)

        return FileResponse(open(pdf_path, "rb"), as_attachment=True, filename=pdf_name)

    except subprocess.TimeoutExpired:
        return JsonResponse({"error": "timeout"}, status=504)

    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# =============================
#       DOCX → PDF
# =============================

def docx_to_pdf(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    f = request.FILES.get("file")
    if not f:
        return HttpResponseBadRequest("No file")

    env = os.environ.copy()
    env["HOME"] = "/tmp"

    workdir = tempfile.mkdtemp(prefix="docx2pdf_", dir="/tmp")

    try:
        in_path = os.path.join(workdir, f.name)
        with open(in_path, "wb") as out:
            for chunk in f.chunks():
                out.write(chunk)

        cmd = [
            "soffice",
            "--headless", "--invisible", "--nodefault", "--nocrashreport",
            "--nolockcheck", "--nologo",
            "--convert-to", "pdf:writer_pdf_Export",
            "--outdir", workdir,
            in_path,
        ]

        completed = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=30, env=env
        )

        if completed.returncode != 0:
            logger.error("LibreOffice failed rc=%s\nstderr=%s",
                         completed.returncode,
                         completed.stderr.decode(errors="ignore"))
            return JsonResponse({"error": "libreoffice-failed"}, status=500)

        pdf_name = os.path.splitext(os.path.basename(in_path))[0] + ".pdf"
        pdf_path = os.path.join(workdir, pdf_name)

        if not os.path.exists(pdf_path):
            return JsonResponse({"error": "pdf-not-produced"}, status=500)

        return FileResponse(open(pdf_path, "rb"), as_attachment=True, filename=pdf_name)

    except subprocess.TimeoutExpired:
        return JsonResponse({"error": "timeout"}, status=504)

    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# =============================
#         Fast Mask API
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
        opts["mask_ratio"] = float(_get("mask_ratio"))

    try:
        out_bytes = mask_pdf_bytes(f.read(), **opts)
    except Exception as e:
        return HttpResponseBadRequest(f"processing error: {e}")

    name_part = os.path.splitext(f.name)[0]
    resp = HttpResponse(out_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{name_part}_masked.pdf"'
    return resp


# =============================
#         AI OCR Mask API
# =============================

@csrf_exempt
def mask_ai_api(request):
    if request.method == "POST" and request.FILES.get("file"):
        try:
            pdf_bytes = request.FILES["file"].read()
            masked_pdf = mask_pdf_bytes_ai(pdf_bytes)

            response = HttpResponse(masked_pdf, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="masked_ai.pdf"'
            return response

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "No file uploaded"}, status=400)
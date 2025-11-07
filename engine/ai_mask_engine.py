# /PDFmaskv2/engine/ai_mask_engine.py

import io
import os
import fitz
import tempfile
from pdf2image import convert_from_bytes
from paddleocr import PaddleOCR

# ===== PaddleOCR 설정 =====
ocr = PaddleOCR(use_angle_cls=True, lang='korean')


def mask_pdf_bytes_ai(pdf_bytes: bytes) -> bytes:
    """
    PaddleOCR 기반 좌표 마스킹 (CPU 완전 호환)
    - PDF → 이미지 변환
    - OCR 텍스트 + 좌표 인식
    - 민감 단어 포함 시 해당 영역 검은색 마스킹
    """
    try:
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = convert_from_bytes(pdf_bytes, dpi=200)

        for idx, img in enumerate(pages):
            tmp_path = tempfile.mktemp(suffix=".jpg")
            img.save(tmp_path)

            result = ocr.ocr(tmp_path)
            page = pdf_doc.load_page(idx)

            if not result or not result[0]:
                os.remove(tmp_path)
                continue

            img_height = img.height

            for line in result[0]:
                try:
                    bbox = line[0]
                    text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])

                    if any(keyword in text for keyword in ["알고리즘", "알고", "리즘", "고리", "알", "고", "리"]):
                        x0, y0 = bbox[0]
                        x1, y1 = bbox[2]
                        y0_pdf = img_height - y1
                        y1_pdf = img_height - y0
                        rect = fitz.Rect(x0, y0_pdf, x1, y1_pdf)
                        page.add_redact_annot(rect, fill=(0, 0, 0))

                except Exception as inner_e:
                    print(f"[WARN] OCR line skipped: {inner_e}")
                    continue


            # --- 페이지별 마스킹 적용 ---
            try:
                page.apply_redactions()  # type: ignore[attr-defined]
            except Exception:
                pass

            os.remove(tmp_path)

        out_buf = io.BytesIO()
        pdf_doc.save(out_buf, garbage=4, deflate=True)
        pdf_doc.close()

        print("[INFO] PaddleOCR masking completed successfully.")
        return out_buf.getvalue()

    except Exception as e:
        print(f"[ERROR] PaddleOCR masking failed: {e}")
        return pdf_bytes
# /PDFmaskv2/engine/ai_mask_engine.py
# 구현 중

import io
import os
import fitz
import tempfile
from pdf2image import convert_from_bytes
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang='korean')

JOSA_SET = {
    "은", "는", "이", "가", "을", "를", "에", "에서", "에게", "께",
    "으로", "로", "으로서", "로서", "으로써", "로써", "에게서",
    "한테", "한테서", "까지", "부터", "처럼", "보다", "와", "과",
    "랑", "이랑", "이나", "나", "이나마", "마다", "조차", "마저",
    "밖에", "도", "만"
}


def mask_pdf_bytes_ai(pdf_bytes: bytes) -> bytes:
    """
    PaddleOCR 기반 조사 앞 단어 실제 마스킹 적용
    - OCR로 텍스트 + 좌표 탐지
    - 조사(은/는/이/가 등) 앞 단어 영역을 실제로 PDF 내에서 가림
    """
    try:
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages = convert_from_bytes(pdf_bytes, dpi=200)

        for idx, img in enumerate(pages):
            tmp_path = tempfile.mktemp(suffix=".jpg")
            img.save(tmp_path)

            result = ocr.ocr(tmp_path)
            page = pdf_doc.load_page(idx)

            img_w, img_h = img.width, img.height
            pdf_w, pdf_h = page.rect.width, page.rect.height
            scale_x = pdf_w / img_w
            scale_y = pdf_h / img_h

            if not result or not result[0]:
                os.remove(tmp_path)
                continue

            for line in result[0]:
                try:
                    if len(line) < 2:
                        continue

                    bbox = line[0]
                    text_info = line[1]
                    text = text_info[0] if isinstance(text_info, (list, tuple)) else str(text_info)
                    text = text.strip()
                    if not text:
                        continue

                    for josa in JOSA_SET:
                        pos = text.find(josa)
                        if pos > 0:
                            prefix = text[:pos].strip()
                            if len(prefix) < 1:
                                continue

                            x0, y0 = bbox[0]
                            x1, y1 = bbox[2]

                            x0_pdf = x0 * scale_x
                            x1_pdf = x1 * scale_x
                            y0_pdf = (img_h - y1) * scale_y
                            y1_pdf = (img_h - y0) * scale_y

                            ratio = len(prefix) / max(len(text), 1)
                            new_x1 = x0_pdf + (x1_pdf - x0_pdf) * ratio

                            rect = fitz.Rect(x0_pdf, y0_pdf, new_x1, y1_pdf)

                            # PDF 내부 가림막 생성
                            annot = page.add_redact_annot(rect, fill=(0, 0, 0))
                            annot.set_colors(stroke=(0, 0, 0))
                            annot.update()

                            break

                except Exception as inner_e:
                    print(f"[WARN] OCR line skipped: {inner_e}")
                    continue

            # 페이지별 실제 적용
            try:
                page.apply_redactions()
            except Exception as apply_e:
                print(f"[WARN] Redaction apply failed: {apply_e}")

            os.remove(tmp_path)

        out_buf = io.BytesIO()
        pdf_doc.save(out_buf, garbage=4, deflate=True)
        pdf_doc.close()

        print("[INFO] PaddleOCR 조사 앞 단어 실제 마스킹 완료 (PDF 내부 반영됨)")
        return out_buf.getvalue()

    except Exception as e:
        print(f"[ERROR] PaddleOCR masking failed: {e}")
        return pdf_bytes

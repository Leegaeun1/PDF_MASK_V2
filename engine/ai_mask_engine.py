# /PDFmaskv2/engine/ai_mask_engine.py
# PaddleOCR 기능 제거, 빈 함수로 대체

def mask_pdf_bytes_ai(pdf_bytes: bytes) -> bytes:
    """
    Dummy function (기능 비활성화 버전)
    - 입력 PDF 바이트를 그대로 반환
    """
    print("[INFO] mask_pdf_bytes_ai(): 기능 비활성화됨 - 원본 PDF 반환")
    return pdf_bytes

# Dockerfile

# 1. 베이스 이미지: Django 5.2+ 버전을 지원하는 파이썬 3.10으로 업그레이드합니다.
FROM python:3.12-bookworm

# 2. 시스템 라이브러리, LibreOffice, 폰트 설치
# Noto CJK 폰트를 설치하여 한국어 처리 호환성을 보장합니다.
RUN apt-get update && apt-get install -y \
    libreoffice \
    fonts-nanum \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 3. 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. 작업 디렉토리 생성
WORKDIR /app

# 5. 의존성 파일 복사 및 설치
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 6. 프로젝트 파일 전체 복사
COPY . .

# 7. 정적 파일 수집
RUN python3 manage.py collectstatic --noinput

# 8. Gunicorn 서버 실행
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--log-level", "debug", "pdfuploader.wsgi:application"]


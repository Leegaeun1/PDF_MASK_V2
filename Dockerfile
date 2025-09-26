# Dockerfile

# 1. 베이스 이미지: 파이썬 3.9 버전이 설치된 가벼운 리눅스 환경으로 시작합니다.
FROM python:3.12-slim

# 2. 환경 변수 설정: 파이썬이 로그를 바로 출력하도록 설정합니다.
ENV PYTHONUNBUFFERED=1

# 3. 작업 디렉토리 생성: 컨테이너 안에 /app 이라는 폴더를 만들고 거기로 이동합니다.
WORKDIR /app

# 4. 의존성 파일 복사: 먼저 requirements.txt 파일만 복사합니다.
COPY requirements.txt requirements.txt

# 5. 의존성 설치: requirements.txt에 명시된 라이브러리들을 설치합니다.
RUN pip install --no-cache-dir -r requirements.txt

# 6. 프로젝트 파일 전체 복사: 현재 폴더(.)의 모든 파일을 컨테이너의 /app 폴더로 복사합니다.
COPY . .

# 7. Gunicorn 서버 실행: 컨테이너가 시작될 때 이 명령어가 실행됩니다.
# 8080 포트를 통해 외부 요청을 받도록 설정합니다.
# 'pdfuploader.wsgi'는 프로젝트의 WSGI 설정 파일을 가리킵니다.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "pdfuploader.wsgi:application"]
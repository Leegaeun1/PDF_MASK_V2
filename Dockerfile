# Debian Bullseye 베이스 이미지 사용 (안정성을 위해)
FROM python:3.11-slim-bookworm

# 1. 시스템 업데이트 및 필수 패키지 설치
# Python 환경, LibreOffice, Java 21, 런타임 패키지 설치
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    # Python 환경 및 유틸리티
    python3 python3-pip python3-venv \
    locales \
    # 1. 'which' 제거함 (패키지명이 아님)
    unzip redis-tools \
    # LibreOffice 및 Java (Bullseye 호환 버전으로 변경)
    libreoffice \
    libreoffice-java-common \
    # 2. Java 21 -> default-jre-headless (Java 11)로 변경
    default-jre-headless \
    # LibreOffice 런타임 안정화 패키지
    fonts-noto-cjk \
    libxext6 libxrender1 libxtst6 fontconfig \
    # ... 아래 정리 명령어는 그대로 유지 ...
    && rm -rf /root/.config/libreoffice \
    && rm -rf /root/.local/share/fonts \
    && fc-cache -f -v \
    && localedef -i en_US -f UTF-8 en_US.UTF-8 \
    && echo "LibreOffice environment initialized." \
    && mkdir -p /tmp/celery_jobs \
    && chmod 777 /tmp/celery_jobs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. 환경 변수 설정 (Java 21 경로 명시)
# Java 21의 설치 경로를 JAVA_HOME으로 설정
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
# 🚨 Java 21 경로로 변경 (Debian에서 표준 설치 경로)
ENV JAVA_HOME /usr/lib/jvm/java-21-openjdk-amd64
ENV PATH $JAVA_HOME/bin:$PATH

WORKDIR /app

# 3. 파이썬 종속성 설치
COPY requirements.txt .
# pip 설치 (Debian 환경의 표준)
RUN pip install --no-cache-dir -r requirements.txt

# 4. Django 프로젝트 및 Entrypoint 설정
COPY . /app
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]

# 5. CMD 정의 (gunicorn 실행)
CMD ["gunicorn", "pdfuploader.wsgi:application", "--bind", "0.0.0.0:8000", "--timeout", "300"]
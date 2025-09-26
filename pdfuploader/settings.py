# settings.py (핵심 부분만)
from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'some-default-secret-key-for-local-dev')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    '.run.app',
    'localhost',
    '127.0.0.1',
]

CSRF_TRUSTED_ORIGINS = [
    'https://*.run.app',
]

INSTALLED_APPS = [
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',
    'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'upload',  # ← 추가
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pdfuploader.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],  # ← 프로젝트 전역 템플릿 폴더
    'APP_DIRS': True,
    'OPTIONS': {'context_processors':[
        'django.template.context_processors.debug','django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages',
    ],},
}]
WSGI_APPLICATION = 'pdfuploader.wsgi.application'

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3','NAME': BASE_DIR / 'db.sqlite3',}} # DB 경로

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# 업로드 파일 설정
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# (선택) 업로드 용량 제한: 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

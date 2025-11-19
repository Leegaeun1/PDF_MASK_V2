# settings.py (핵심 부분만)
from pathlib import Path
import os

# 최상위 폴더가 어디인지
BASE_DIR = Path(__file__).resolve().parent.parent 

'''보안을 위한 암호화 키. 로컬 개발 시에는 SECRET_KEY라는 환경 변수 없으니까 뒤에 있는 임시 키를 사용함.
	 GCP 배포 시에는 gcloud 명령어를 통해 SECRET_KEY 환경 변수에 나의 시크릿 키를 설정하게됨
'''
SECRET_KEY = os.environ.get('SECRET_KEY', 'some-default-secret-key-for-local-dev')

'''DEBUG 가 True이면 개발 모드. 오류 발생 시 자세한 디버깅 정보 보여줌. 
						False이면 실제 서비스 모드. 사용자에게 간단한 오류 페이지만 보여줌. 자동으로 False'''
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# WSL에서 favicon.ico 출력하기
if os.environ.get('WSL_DEV', 'False') == 'True':
    DEBUG = True

# 이 웹사이트에서 접속을 허용할 도메인 주소 목록. 
ALLOWED_HOSTS = [
    '.run.app',
    'localhost',
    '127.0.0.1',
    'gnupdf.com', 
    'www.gnupdf.com' # 현재는 shop으로 등록했으나 com으로 바꿀예정임
]

# https환경에서 POST 요청을 보낼때, 해당 요청이 신뢰할 수 있는 출처에서 왔는지 검사
CSRF_TRUSTED_ORIGINS = [
    'https://*.run.app',
    'https://*.gnupdf.com',
]

# settings.py
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") # https이면 요청이 안전하다고 판단함!
USE_X_FORWARDED_HOST = True  # 절대 URL 생성(build_absolute_uri) 시 Host 신뢰

'''이 프로젝트를 구성하는 앱들의 목록. upload를 추가한 이유가 우리의 핵심 기능인 PDF 업로드 및 처리가 들어가서.
	 이때, 앱은 Django의 기능과 직접적으로 연결되는것을 뜻함.
'''
INSTALLED_APPS = [
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',
    'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'upload',  # ← 추가
]
# 여러 검문소 목록. 보안 등..
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',  # 반드시 맨 위
    'django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
# 사용자가 url 요청 시 어떤 urls.py 파일을 가장 먼저 참고해야하는지 알려줌.
ROOT_URLCONF = 'pdfuploader.urls'

# 사용자에게 보여줄 html파일들을 어디서 찾을지(DIRS), 어떻게 처리할지.
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],  # 프로젝트 전역 템플릿 폴더
    'APP_DIRS': True,
    'OPTIONS': {'context_processors':[
        'django.template.context_processors.debug','django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages',
    ],},
}]
WSGI_APPLICATION = 'pdfuploader.wsgi.application'

# 프로젝트가 사용할 데이터베이스 설정
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3','NAME': BASE_DIR / 'db.sqlite3',}} # DB 경로

# 정적 파일 설정
STATIC_URL = '/static/'

if DEBUG:
    STATICFILES_DIRS = [BASE_DIR / 'static']
else:
    STATICFILES_DIRS = []  # 운영 환경에서는 비활성화

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 미디어 파일
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 업로드 용량 제한: 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

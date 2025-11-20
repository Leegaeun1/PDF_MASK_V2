import os
from celery import Celery

# 1. Django 설정 로드
# 이 환경 변수가 Worker가 Django 설정을 찾게 해줍니다.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pdfuploader.settings') 

# 2. Celery 인스턴스 생성
app = Celery('pdfuploader')

# 3. Django 설정에서 CELERY_ 접두사가 붙은 설정을 로드합니다.
app.config_from_object('django.conf:settings', namespace='CELERY')

# 4. Task 자동 탐색
# 설치된 Django 앱 (upload 포함) 내의 tasks.py 파일을 자동으로 찾습니다.
app.autodiscover_tasks()
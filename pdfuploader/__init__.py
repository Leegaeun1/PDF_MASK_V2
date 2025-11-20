# 이 파일이 프로젝트의 루트 디렉터리에 있는지 확인합니다.
from .celery import app as celery_app

# 이 코드는 Celery Worker가 시작될 때 Task가 로드되도록 합니다.
__all__ = ('celery_app',)
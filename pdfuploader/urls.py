# /pdfuploader/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView  # favicon redirect용

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('upload.urls')),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.ico')),  # 한 줄 추가
]

# 개발 환경: STATICFILES_DIRS + MEDIA 서빙
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 운영 환경: STATIC_ROOT 서빙
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
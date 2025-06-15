from django.urls import path
from .views import GenerateDocsView
# Импорт новых представлений
from .views import DocumentListView, DocumentGenerateView, DocumentDownloadPdfView, DocumentDownloadHtmlView, UploadFileView, GenerateLocalDocsView, DocumentDeleteView, RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('generate-docs/', GenerateDocsView.as_view(), name='generate-docs'),
    path('documents/', DocumentListView.as_view(), name='documents-list'),
    path('documents/generate/', DocumentGenerateView.as_view(), name='documents-generate'),
    path('documents/<int:pk>/', DocumentDeleteView.as_view(), name='documents-delete'),
    path('documents/<int:pk>/download_pdf', DocumentDownloadPdfView.as_view(), name='documents-download-pdf'),
    path('documents/<int:pk>/download_html', DocumentDownloadHtmlView.as_view(), name='documents-download-html'),
    path('upload', UploadFileView.as_view(), name='upload-file'),
    path('generate-local-docs/', GenerateLocalDocsView.as_view(), name='generate-local-docs'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

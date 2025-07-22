from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PredictionJobViewSet, CellMetricsViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'predictions', PredictionJobViewSet, basename='predictions')
router.register(r'metrics', CellMetricsViewSet, basename='metrics')

urlpatterns = [
    path('', include(router.urls)),
]


from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ProfileViewSet, CategoryViewSet, ResourceViewSet, TagViewSet, top_resources

router = DefaultRouter()
router.register('profiles', ProfileViewSet)
router.register('categories', CategoryViewSet)
router.register('resources', ResourceViewSet)
router.register('tags', TagViewSet)

urlpatterns = router.urls + [
    path('top-resources/', top_resources),
]

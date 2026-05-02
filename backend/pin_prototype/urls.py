from rest_framework.routers import DefaultRouter
from .views import ProfileViewSet, CategoryViewSet, ResourceViewSet, TagViewSet

router = DefaultRouter()
router.register('profiles', ProfileViewSet)
router.register('categories', CategoryViewSet)
router.register('resources', ResourceViewSet)
router.register('tags', TagViewSet)

urlpatterns = router.urls

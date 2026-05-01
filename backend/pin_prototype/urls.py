from rest_framework.routers import DefaultRouter
from .views import ProfileViewSet, CategoryViewSet, ResourceViewSet

router = DefaultRouter()
router.register('profiles', ProfileViewSet)
router.register('categories', CategoryViewSet)
router.register('resources', ResourceViewSet)

urlpatterns = router.urls

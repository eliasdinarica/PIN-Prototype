from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    ProfileViewSet, CategoryViewSet, ResourceViewSet, TagViewSet,
    ResourceFeedbackViewSet, AudienceViewSet, CategoryBriefViewSet,
    GuideViewSet, top_resources, editor_image_upload, chat_view, search_data,
)
from .tts import tts_view

router = DefaultRouter()
router.register('profiles', ProfileViewSet)
router.register('categories', CategoryViewSet)
router.register('categories-brief', CategoryBriefViewSet, basename='categories-brief')
router.register('audiences', AudienceViewSet)
router.register('resources', ResourceViewSet, basename='resources')
router.register('tags', TagViewSet)
router.register('feedback', ResourceFeedbackViewSet, basename='feedback')
router.register('guides', GuideViewSet, basename='guide')

urlpatterns = router.urls + [
    path('top-resources/', top_resources),
    path('search/', search_data),
    path('editor/image/', editor_image_upload),
    path('chat/', chat_view),
    path('tts/', tts_view),
]

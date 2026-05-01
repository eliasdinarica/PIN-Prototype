from rest_framework.viewsets import ModelViewSet
from .models import Profile, Category, Resource
from .serializers import ProfileSerializer, CategorySerializer, ResourceSerializer


class ProfileViewSet(ModelViewSet):
    queryset = Profile.objects.all().order_by('-created_at')
    serializer_class = ProfileSerializer


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ResourceViewSet(ModelViewSet):
    queryset = Resource.objects.all().order_by('name')
    serializer_class = ResourceSerializer

from rest_framework import serializers
from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'language', 'has_children', 'created_at']
        read_only_fields = ['id', 'created_at']

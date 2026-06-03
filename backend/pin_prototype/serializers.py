from rest_framework import serializers
from .models import Profile, Category, Subcategory, Resource, Tag, Audience, ResourceFeedback, Attachment, Pathway, PathwayStep


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'id', 'language', 'other_languages', 'status', 'has_children',
            'arrived_over_year_ago', 'birth_date',
            'has_driving_license', 'computer_skills', 'education_level',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ResourceFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceFeedback
        fields = ['id', 'profile', 'resource', 'is_useful', 'created_at']
        read_only_fields = ['id', 'created_at']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'label']


class AudienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audience
        fields = ['id', 'name']


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'order', 'file', 'label']
        read_only_fields = ['id']


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'order']


class ResourceSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    subcategory = SubcategorySerializer(read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), source='tags', write_only=True, required=False
    )
    audience_ids = serializers.PrimaryKeyRelatedField(
        many=True, source='audiences', read_only=True
    )

    class Meta:
        model = Resource
        fields = [
            'id', 'category', 'subcategory', 'audiences', 'audience_ids', 'tags', 'tag_ids',
            'name', 'description', 'body', 'attachments', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'audiences', 'audience_ids', 'subcategory']


class CategorySerializer(serializers.ModelSerializer):
    resources = ResourceSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'icon', 'resources']


class CategoryBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon']


class PathwayStepSerializer(serializers.ModelSerializer):
    resource = ResourceSerializer(read_only=True)

    class Meta:
        model = PathwayStep
        fields = ['id', 'order', 'step_label', 'resource']


class PathwayBriefSerializer(serializers.ModelSerializer):
    step_count = serializers.SerializerMethodField()

    def get_step_count(self, obj):
        return obj.steps.count()

    class Meta:
        model = Pathway
        fields = ['id', 'title', 'description', 'icon', 'step_count', 'order']


class PathwaySerializer(serializers.ModelSerializer):
    steps = PathwayStepSerializer(many=True, read_only=True)
    step_count = serializers.SerializerMethodField()

    def get_step_count(self, obj):
        return obj.steps.count()

    class Meta:
        model = Pathway
        fields = ['id', 'title', 'description', 'icon', 'step_count', 'order', 'steps']

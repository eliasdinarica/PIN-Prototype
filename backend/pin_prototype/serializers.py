import re

from django.conf import settings
from rest_framework import serializers
from wagtail.rich_text import expand_db_html
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


def _absolutize_urls(html):
    """Rewrite root-relative media/document URLs (Wagtail images & document
    links) to absolute backend URLs so they work from the separate frontend."""
    base = (getattr(settings, 'WAGTAILADMIN_BASE_URL', '') or '').rstrip('/')
    if not base:
        return html
    return re.sub(r'(src|href)="(/(?:media|documents)/)', rf'\1="{base}\2', html)


BASE_LANG = 'fr'  # Language the resource content is authored in.


def render_section_values(why, how, location):
    """Build the fixed-section list from raw field values."""
    result = []
    for key, value in (('why', why), ('how', how), ('location', location)):
        if value and str(value).strip():
            result.append({'key': key, 'html': _absolutize_urls(expand_db_html(str(value)))})
    return result


def render_sections(obj):
    return render_section_values(obj.why_interesting, obj.how_to, obj.location)


class ResourceSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    subcategory = SubcategorySerializer(read_only=True)
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()
    places = serializers.SerializerMethodField()
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), source='tags', write_only=True, required=False
    )
    audience_ids = serializers.PrimaryKeyRelatedField(
        many=True, source='audiences', read_only=True
    )

    def _translation(self, obj):
        """Return the ResourceTranslation matching the requested ?lang, or None."""
        request = self.context.get('request')
        params = getattr(request, 'query_params', None) or getattr(request, 'GET', {})
        lang = params.get('lang') if request else None
        if not lang or lang == BASE_LANG:
            return None
        return next((t for t in obj.translations.all() if t.language == lang), None)

    def get_name(self, obj):
        tr = self._translation(obj)
        return tr.name if (tr and tr.name) else obj.name

    def get_description(self, obj):
        tr = self._translation(obj)
        return tr.description if (tr and tr.description) else obj.description

    def get_sections(self, obj):
        try:
            tr = self._translation(obj)
            if tr:
                return render_section_values(
                    tr.why_interesting or obj.why_interesting,
                    tr.how_to or obj.how_to,
                    tr.location or obj.location,
                )
            return render_sections(obj)
        except Exception:
            return []

    def get_languages(self, obj):
        return [BASE_LANG] + sorted({t.language for t in obj.translations.all()})

    def get_author(self, obj):
        return obj.author.name if obj.author_id else 'COSM'

    def get_places(self, obj):
        return [
            {
                'name': p.name, 'city': p.city, 'address': p.address,
                'phone': p.phone, 'email': p.email,
                'lat': p.latitude, 'lng': p.longitude,
            }
            for p in obj.places.all()
        ]

    class Meta:
        model = Resource
        fields = [
            'id', 'category', 'subcategory', 'audiences', 'audience_ids', 'tags', 'tag_ids',
            'name', 'description', 'sections', 'author', 'languages', 'places', 'attachments', 'created_at',
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
    category = serializers.SerializerMethodField()

    def get_step_count(self, obj):
        return obj.steps.count()

    def get_category(self, obj):
        return {'id': obj.category_id, 'name': obj.category.name} if obj.category_id else None

    class Meta:
        model = Pathway
        fields = ['id', 'title', 'description', 'icon', 'step_count', 'order', 'category', 'steps']

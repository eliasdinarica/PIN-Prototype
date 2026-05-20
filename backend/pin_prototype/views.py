from datetime import date as date_cls
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from .models import Profile, Audience, Category, Resource, Tag, ResourceFeedback, Attachment
from .serializers import (
    ProfileSerializer, CategorySerializer, ResourceSerializer,
    TagSerializer, ResourceFeedbackSerializer, AudienceSerializer,
    CategoryBriefSerializer,
)


def _compute_age(birth_date):
    if not birth_date:
        return None
    today = date_cls.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def _audience_matches(audience, profile, age):
    if audience.statuses:
        allowed = [s.strip() for s in audience.statuses.split(',')]
        if profile.status not in allowed:
            return False

    if audience.has_children is not None:
        if profile.has_children != audience.has_children:
            return False

    if audience.origin_sectors:
        allowed = [s.strip() for s in audience.origin_sectors.split(',')]
        if profile.origin_sector not in allowed:
            return False

    if audience.arrived_over_year is not None:
        if profile.arrived_over_year_ago != audience.arrived_over_year:
            return False

    if audience.min_age is not None and age is not None:
        if age < audience.min_age:
            return False

    if audience.max_age is not None and age is not None:
        if age > audience.max_age:
            return False

    return True


def _matched_tag_ids(profile):
    age = _compute_age(profile.birth_date)
    tag_ids = set()
    for audience in Audience.objects.prefetch_related('relevant_tags').all():
        if _audience_matches(audience, profile, age):
            tag_ids.update(t.id for t in audience.relevant_tags.all())
    return tag_ids


def _load_feedback(profile):
    """Returns {resource_id: (is_useful, frozenset(tag_ids))} for all feedbacks of this profile."""
    result = {}
    for fb in ResourceFeedback.objects.filter(profile=profile).prefetch_related('resource__tags'):
        result[fb.resource_id] = (fb.is_useful, frozenset(t.id for t in fb.resource.tags.all()))
    return result


def _apply_feedback(base_score, resource_id, resource_tag_ids, feedback):
    """Adjust base score using direct feedback and tag-similarity to other feedbacks."""
    if not feedback:
        return float(base_score)

    direct = feedback.get(resource_id)
    if direct is not None:
        is_useful, _ = direct
        if not is_useful:
            return -1.0  # always lands in "others", sorted below unrated resources
        base_score += 2.0

    for fb_id, (is_useful, fb_tags) in feedback.items():
        if fb_id == resource_id:
            continue
        if len(resource_tag_ids & fb_tags) >= 2:
            base_score += 1 if is_useful else -1

    return max(0.0, float(base_score))



class ProfileViewSet(ModelViewSet):
    queryset = Profile.objects.all().order_by('-created_at')
    serializer_class = ProfileSerializer


class ResourceFeedbackViewSet(ModelViewSet):
    serializer_class = ResourceFeedbackSerializer
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        qs = ResourceFeedback.objects.all()
        profile_id = self.request.query_params.get('profile')
        if profile_id:
            qs = qs.filter(profile_id=profile_id)
        return qs

    def create(self, request, *args, **kwargs):
        profile_id = request.data.get('profile')
        resource_id = request.data.get('resource')
        is_useful = request.data.get('is_useful')
        feedback, created = ResourceFeedback.objects.update_or_create(
            profile_id=profile_id,
            resource_id=resource_id,
            defaults={'is_useful': is_useful},
        )
        serializer = self.get_serializer(feedback)
        return Response(serializer.data, status=201 if created else 200)


class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

    def get_queryset(self):
        return Category.objects.prefetch_related(
            'audiences', 'audiences__relevant_tags',
            'resources', 'resources__tags', 'resources__audiences',
            'resources__attachments',
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        profile_id = request.query_params.get('profile')

        if profile_id:
            try:
                profile = Profile.objects.get(pk=profile_id)
                age = _compute_age(profile.birth_date)

                recommended = []
                universal = []
                deprioritized = []
                for cat in queryset:
                    audiences = list(cat.audiences.all())
                    if not audiences:
                        universal.append(cat)
                    else:
                        matches = sum(1 for a in audiences if _audience_matches(a, profile, age))
                        if matches > 0:
                            recommended.append((cat, matches))
                        else:
                            deprioritized.append(cat)

                recommended.sort(key=lambda x: (-x[1], -x[0].priority, x[0].name))
                universal.sort(key=lambda c: (-c.priority, c.name))
                deprioritized.sort(key=lambda c: (-c.priority, c.name))
                ordered = (
                    [(cat, True) for cat, _ in recommended]
                    + [(cat, False) for cat in universal]
                    + [(cat, False) for cat in deprioritized]
                )
            except Profile.DoesNotExist:
                ordered = [(cat, False) for cat in queryset.order_by('-priority', 'name')]
        else:
            ordered = [(cat, False) for cat in queryset.order_by('-priority', 'name')]

        serializer = self.get_serializer([cat for cat, _ in ordered], many=True)
        data = [{**item, 'is_recommended': is_rec} for item, (_, is_rec) in zip(serializer.data, ordered)]
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = dict(serializer.data)

        profile_id = request.query_params.get('profile')
        if profile_id:
            try:
                profile = Profile.objects.get(pk=profile_id)
                tag_ids = _matched_tag_ids(profile)
                feedback = _load_feedback(profile)
                age = _compute_age(profile.birth_date)
                all_audiences = {a.id: a for a in Audience.objects.all()}

                def score(r):
                    r_tag_ids = frozenset(t['id'] for t in r.get('tags', []))

                    # Direct feedback overrides audience gates
                    direct = feedback.get(r['id'])
                    if direct is not None:
                        is_useful, _ = direct
                        if not is_useful:
                            return -1.0
                        # Directly liked → always recommended regardless of audience
                        tag_bonus = len(r_tag_ids & tag_ids) * 0.5
                        sim_bonus = sum(
                            0.5 if fb_useful else -0.5
                            for fb_id, (fb_useful, fb_tags) in feedback.items()
                            if fb_id != r['id'] and len(r_tag_ids & fb_tags) >= 2
                        )
                        return max(0.0, 1000.0 + tag_bonus + sim_bonus)

                    aid_list = r.get('audience_ids', [])
                    if not aid_list:
                        return 0
                    audience_matches = sum(
                        1 for aid in aid_list
                        if aid in all_audiences and _audience_matches(all_audiences[aid], profile, age)
                    )
                    if audience_matches == 0:
                        return 0
                    tag_overlap = len(r_tag_ids & tag_ids)
                    if tag_overlap == 0:
                        return 0  # audience match alone isn't enough — needs at least 1 relevant tag
                    raw = audience_matches + tag_overlap * 0.5
                    return _apply_feedback(raw, r['id'], r_tag_ids, feedback)

                scored = sorted([(r, score(r)) for r in data['resources']], key=lambda x: -x[1])
                data['resources'] = [{**r, 'is_recommended': s > 0} for r, s in scored]
            except Profile.DoesNotExist:
                data['resources'] = [{**r, 'is_recommended': False} for r in data['resources']]
        else:
            data['resources'] = [{**r, 'is_recommended': False} for r in data['resources']]

        return Response(data)


@api_view(['GET'])
def top_resources(request):
    profile_id = request.query_params.get('profile')
    limit = min(int(request.query_params.get('limit', 8)), 20)

    if not profile_id:
        return Response([])
    try:
        profile = Profile.objects.get(pk=profile_id)
    except Profile.DoesNotExist:
        return Response([])

    tag_ids = _matched_tag_ids(profile)
    if not tag_ids:
        return Response([])

    feedback = _load_feedback(profile)
    age = _compute_age(profile.birth_date)
    results = []
    for cat in Category.objects.prefetch_related(
        'resources__tags', 'resources__audiences', 'resources__attachments',
    ).all():
        for resource in cat.resources.all():
            resource_tag_ids = frozenset(t.id for t in resource.tags.all())
            direct = feedback.get(resource.id)

            if direct is not None and direct[0]:
                # Directly liked → always in "for you", score computed without _apply_feedback to avoid double-count
                sim_bonus = sum(
                    0.5 if fb_useful else -0.5
                    for fb_id, (fb_useful, fb_tags) in feedback.items()
                    if fb_id != resource.id and len(resource_tag_ids & fb_tags) >= 2
                )
                adjusted = max(0.0, 1000.0 + len(resource_tag_ids & tag_ids) * 0.5 + sim_bonus)
            else:
                if direct is not None and not direct[0]:
                    continue  # disliked → skip entirely
                r_audiences = list(resource.audiences.all())
                if not r_audiences:
                    continue
                audience_matches = sum(1 for a in r_audiences if _audience_matches(a, profile, age))
                if audience_matches == 0:
                    continue
                raw = audience_matches + len(resource_tag_ids & tag_ids) * 0.5
                adjusted = _apply_feedback(raw, resource.id, resource_tag_ids, feedback)
            if adjusted > 0:
                data = ResourceSerializer(resource, context={'request': request}).data
                results.append({**data, 'score': adjusted, 'category': {'id': cat.id, 'name': cat.name}})

    results.sort(key=lambda x: -x['score'])
    return Response(results[:limit])


class ResourceViewSet(ModelViewSet):
    serializer_class = ResourceSerializer

    def get_queryset(self):
        qs = Resource.objects.prefetch_related(
            'tags', 'audiences', 'attachments',
        ).select_related('category').order_by('name')
        category_id = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        if category_id:
            qs = qs.filter(category_id=category_id)
        if search:
            qs = qs.filter(name__icontains=search)
        return qs

    @staticmethod
    def _parse_json(data, key, default):
        import json
        raw = data.get(key, None)
        if raw is None:
            return default
        return json.loads(raw) if isinstance(raw, str) else raw

    def create(self, request, *args, **kwargs):
        data = request.data
        body = self._parse_json(data, 'body', {'blocks': []})
        attachment_meta = self._parse_json(data, 'attachments_meta', [])
        tag_ids = data.getlist('tag_ids') if hasattr(data, 'getlist') else data.get('tag_ids', [])

        resource = Resource.objects.create(
            category_id=data.get('category'),
            name=data.get('name', ''),
            description=data.get('description', ''),
            body=body,
        )
        resource.tags.set([int(t) for t in tag_ids if t])

        files = request.FILES.getlist('attachment_files') if hasattr(request.FILES, 'getlist') else []
        for idx, f in enumerate(files):
            label = attachment_meta[idx].get('label', '') if idx < len(attachment_meta) else ''
            order = attachment_meta[idx].get('order', idx) if idx < len(attachment_meta) else idx
            Attachment.objects.create(resource=resource, file=f, label=label, order=order)

        return Response(ResourceSerializer(resource, context={'request': request}).data, status=201)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data

        if 'category' in data:
            instance.category_id = data.get('category')
        if 'name' in data:
            instance.name = data.get('name', '')
        if 'description' in data:
            instance.description = data.get('description', '')
        if 'body' in data:
            instance.body = self._parse_json(data, 'body', {'blocks': []})
        instance.save()

        if 'tag_ids' in data:
            tag_ids = data.getlist('tag_ids') if hasattr(data, 'getlist') else data.get('tag_ids', [])
            instance.tags.set([int(t) for t in tag_ids if t])

        # Attachments: keep only those listed in kept_attachments, add new files
        if 'kept_attachments' in data:
            kept = self._parse_json(data, 'kept_attachments', [])
            kept_ids = {int(k['id']) for k in kept if k.get('id')}
            instance.attachments.exclude(id__in=kept_ids).delete()
            for k in kept:
                if k.get('id'):
                    Attachment.objects.filter(id=int(k['id'])).update(
                        label=k.get('label', ''), order=k.get('order', 0),
                    )

        new_meta = self._parse_json(data, 'new_attachments_meta', [])
        files = request.FILES.getlist('new_attachment_files') if hasattr(request.FILES, 'getlist') else []
        existing_count = instance.attachments.count()
        for idx, f in enumerate(files):
            label = new_meta[idx].get('label', '') if idx < len(new_meta) else ''
            order = new_meta[idx].get('order', existing_count + idx) if idx < len(new_meta) else existing_count + idx
            Attachment.objects.create(resource=instance, file=f, label=label, order=order)

        return Response(ResourceSerializer(instance, context={'request': request}).data)


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all().order_by('label')
    serializer_class = TagSerializer


class AudienceViewSet(ReadOnlyModelViewSet):
    queryset = Audience.objects.all().order_by('name')
    serializer_class = AudienceSerializer


class CategoryBriefViewSet(ReadOnlyModelViewSet):
    """Lightweight category list for the admin form (no resources/recommendations)."""
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategoryBriefSerializer


@api_view(['POST'])
@parser_classes([MultiPartParser])
def editor_image_upload(request):
    """Endpoint for Editor.js image plugin. Expects field name 'image'."""
    image = request.FILES.get('image')
    if not image:
        return Response({'success': 0, 'message': 'No image provided'}, status=400)
    path = default_storage.save(f'articles/{image.name}', ContentFile(image.read()))
    url = default_storage.url(path)
    if request and not url.startswith('http'):
        url = request.build_absolute_uri(url)
    return Response({'success': 1, 'file': {'url': url}})

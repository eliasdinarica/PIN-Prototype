from datetime import date as date_cls
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Profile, Audience, Category, Resource, Tag
from .serializers import ProfileSerializer, CategorySerializer, ResourceSerializer, TagSerializer


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


class ProfileViewSet(ModelViewSet):
    queryset = Profile.objects.all().order_by('-created_at')
    serializer_class = ProfileSerializer


class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

    def get_queryset(self):
        return Category.objects.prefetch_related(
            'audiences', 'audiences__relevant_tags',
            'resources', 'resources__tags',
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

                def score(r):
                    return len({t['id'] for t in r.get('tags', [])} & tag_ids)

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

    results = []
    for cat in Category.objects.prefetch_related('resources__tags').all():
        for resource in cat.resources.all():
            resource_tag_ids = {t.id for t in resource.tags.all()}
            score = len(resource_tag_ids & tag_ids)
            if score > 0:
                data = ResourceSerializer(resource, context={'request': request}).data
                results.append({**data, 'score': score, 'category': {'id': cat.id, 'name': cat.name}})

    results.sort(key=lambda x: -x['score'])
    return Response(results[:limit])


class ResourceViewSet(ModelViewSet):
    queryset = Resource.objects.all().order_by('name')
    serializer_class = ResourceSerializer


class TagViewSet(ModelViewSet):
    queryset = Tag.objects.all().order_by('label')
    serializer_class = TagSerializer

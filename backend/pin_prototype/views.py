from datetime import date as date_cls
from django.db.models import Prefetch
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from .models import Profile, Audience, Category, Resource, Tag, ResourceFeedback, Attachment, Guide
from .serializers import (
    ProfileSerializer, CategorySerializer, ResourceSerializer,
    TagSerializer, ResourceFeedbackSerializer, AudienceSerializer,
    CategoryBriefSerializer, GuideBriefSerializer, GuideSerializer,
    render_sections,
)


_COMPUTER_SKILLS_ORDER = {'none': 0, 'basic': 1, 'advanced': 2}
_EDUCATION_LEVEL_ORDER = {'primary': 0, 'secondary': 1, 'vocational': 2, 'bachelor': 3, 'master_plus': 4}


def _audience_matches(audience, profile):
    if audience.statuses:
        allowed = [s.strip() for s in audience.statuses.split(',')]
        if profile.status not in allowed:
            return False

    if audience.has_children is not None:
        if profile.has_children != audience.has_children:
            return False

    if audience.arrived_over_year is not None:
        if profile.arrived_over_year_ago != audience.arrived_over_year:
            return False

    if audience.has_driving_license is not None:
        if bool(profile.has_driving_license) != audience.has_driving_license:
            return False

    if audience.min_computer_skills:
        profile_level = _COMPUTER_SKILLS_ORDER.get(profile.computer_skills or 'none', 0)
        required_level = _COMPUTER_SKILLS_ORDER.get(audience.min_computer_skills, 0)
        if profile_level < required_level:
            return False

    if audience.min_education_level:
        profile_level = _EDUCATION_LEVEL_ORDER.get(profile.education_level or 'primary', 0)
        required_level = _EDUCATION_LEVEL_ORDER.get(audience.min_education_level, 0)
        if profile_level < required_level:
            return False

    return True


def _matched_tag_ids(profile):
    tag_ids = set()
    for audience in Audience.objects.prefetch_related('relevant_tags').all():
        if _audience_matches(audience, profile):
            tag_ids.update(t.id for t in audience.relevant_tags.all())
    return tag_ids


COMMUNITY_MIN_LIKES = 2          # how many similar profiles must like a resource
SIMILARITY_THRESHOLD = 0.5       # min share of shared attributes that must match
AFFINITY_TAG_WEIGHT = 0.5        # ranking boost per tag shared with saved/liked


def _compute_age(birth_date):
    if not birth_date:
        return None
    today = date_cls.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def _age_bracket(birth_date):
    age = _compute_age(birth_date)
    if age is None:
        return None
    for hi, label in ((26, '18-25'), (36, '26-35'), (51, '36-50'), (66, '51-65')):
        if age < hi:
            return label
    return '65+'


def _profile_attrs(profile):
    """Comparable attributes of a profile. Unanswered fields are omitted so they
    neither match nor penalise the similarity."""
    attrs = {}
    if profile.language:
        attrs['language'] = profile.language
    if profile.status and profile.status != 'other':
        attrs['status'] = profile.status
    if profile.french_level:
        attrs['french_level'] = profile.french_level
    if profile.has_children is not None:
        attrs['has_children'] = profile.has_children
    if profile.arrived_over_year_ago is not None:
        attrs['arrived_over_year_ago'] = profile.arrived_over_year_ago
    if profile.computer_skills:
        attrs['computer_skills'] = profile.computer_skills
    if profile.education_level:
        attrs['education_level'] = profile.education_level
    if profile.origin_sector:
        attrs['origin_sector'] = profile.origin_sector
    bracket = _age_bracket(profile.birth_date)
    if bracket:
        attrs['age_bracket'] = bracket
    return attrs


def _similarity(a, b):
    """Share of the attributes present in both profiles that hold the same value."""
    common = a.keys() & b.keys()
    if not common:
        return 0.0
    matches = sum(1 for k in common if a[k] == b[k])
    return matches / len(common)


def _similar_liked(profile):
    """Resource ids liked by >= COMMUNITY_MIN_LIKES profiles whose overall
    similarity to this one exceeds SIMILARITY_THRESHOLD. Replaces the former
    per-criterion cohorts (same language / same status) with a single, richer
    notion of 'people whose situation resembles yours'."""
    me = _profile_attrs(profile)
    if not me:
        return set()
    feedbacks = (
        ResourceFeedback.objects
        .filter(is_useful=True)
        .exclude(profile_id=profile.pk)
        .select_related('profile')
    )
    sim_cache = {}
    counts = {}
    for fb in feedbacks:
        sim = sim_cache.get(fb.profile_id)
        if sim is None:
            sim = _similarity(me, _profile_attrs(fb.profile))
            sim_cache[fb.profile_id] = sim
        if sim >= SIMILARITY_THRESHOLD:
            counts[fb.resource_id] = counts.get(fb.resource_id, 0) + 1
    return {rid for rid, n in counts.items() if n >= COMMUNITY_MIN_LIKES}


def _affinity_tags(source_ids):
    """Tag ids drawn from the resources a person saved or liked. Used to surface
    other resources sharing those tags (content-based personal signal)."""
    if not source_ids:
        return set()
    tags = set()
    for r in Resource.objects.filter(id__in=source_ids).prefetch_related('tags'):
        tags.update(t.id for t in r.tags.all())
    return tags


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
        approved = (
            Resource.objects.filter(status=Resource.STATUS_APPROVED)
            .select_related('subcategory', 'author')
            .prefetch_related('tags', 'attachments', 'places', 'translations')
        )
        return Category.objects.prefetch_related(
            'audiences', 'audiences__relevant_tags',
            Prefetch('resources', queryset=approved),
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().order_by('-priority', 'name')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
                    r_tag_ids = frozenset(t['id'] for t in r.get('tags', []))
                    tag_overlap = len(r_tag_ids & tag_ids)
                    if tag_overlap == 0:
                        return 0, False
                    return tag_overlap * 0.5, tag_overlap >= 2

                scored = sorted([(r, score(r)) for r in data['resources']], key=lambda x: -x[1][0])
                similar_likes = _similar_liked(profile)
                data['resources'] = [
                    {
                        **r,
                        'is_recommended': s > 0,
                        'recommended_by_system': rec,
                        'recommended_by_similar': r['id'] in similar_likes,
                        'recommended_by_affinity': False,
                    }
                    for r, (s, rec) in scored
                ]
            except Profile.DoesNotExist:
                data['resources'] = [{**r, 'is_recommended': False, 'recommended_by_system': False, 'recommended_by_similar': False, 'recommended_by_affinity': False} for r in data['resources']]
        else:
            data['resources'] = [{**r, 'is_recommended': False, 'recommended_by_system': False, 'recommended_by_similar': False, 'recommended_by_affinity': False} for r in data['resources']]

        # Guides shown under this category (co-located with resources).
        guides = (
            instance.guides.filter(is_active=True).order_by('order')
            .prefetch_related(
                'steps__resource__tags', 'steps__resource__places',
                'steps__resource__attachments', 'steps__resource__translations',
                'translations',
            )
        )
        data['guides'] = GuideSerializer(guides, many=True, context={'request': request}).data

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

    similar_likes = _similar_liked(profile)
    results = []
    for cat in Category.objects.prefetch_related(
        'resources__tags', 'resources__attachments', 'resources__subcategory', 'resources__places',
    ).all():
        for resource in cat.resources.all():
            if resource.status != Resource.STATUS_APPROVED:
                continue
            resource_tag_ids = frozenset(t.id for t in resource.tags.all())
            tag_overlap = len(resource_tag_ids & tag_ids)
            if tag_overlap == 0:
                continue
            score = tag_overlap * 0.5
            data = ResourceSerializer(resource, context={'request': request}).data
            results.append({
                **data,
                'score': score,
                'category': {'id': cat.id, 'name': cat.name},
                'recommended_by_system': tag_overlap >= 2,
                'recommended_by_similar': resource.id in similar_likes,
            })

    results.sort(key=lambda x: -x['score'])
    return Response(results[:limit])


def _rank_by_profile(items, name_key, profile, tag_ids,
                     similar_likes, affinity_tags, affinity_exclude):
    """Annotate serialized items (resources or guides) with recommendation flags
    and sort them so recommended ones bubble up. Three independent signals:

    - system: the item carries tags flagged as relevant by the audiences the
      profile matches (the tag is the sole bridge between a profile and content).
    - similar: liked by enough profiles whose situation resembles this one.
    - affinity: shares tags with what the person saved or liked (content-based).

    Guides carry no feedback and are not saved as resources, so they are called
    with empty similar/affinity sets and receive the system signal only."""
    def score(it):
        it_tag_ids = frozenset(t['id'] for t in it.get('tags', []))
        overlap = len(it_tag_ids & tag_ids)
        if overlap == 0:
            return 0, False
        return overlap * 0.5, overlap >= 2

    for it in items:
        s, rec = score(it)
        similar = it['id'] in similar_likes
        affinity = 0.0
        if affinity_tags and it['id'] not in affinity_exclude:
            it_tag_ids = frozenset(t['id'] for t in it.get('tags', []))
            overlap = len(it_tag_ids & affinity_tags)
            # Require >= 2 shared tags so a single generic tag (e.g. "Travail")
            # doesn't flag half the catalogue. Keeps the signal granular.
            if overlap >= 2:
                affinity = overlap * AFFINITY_TAG_WEIGHT
        it['recommended_by_system'] = rec
        it['recommended_by_similar'] = similar
        it['recommended_by_affinity'] = affinity > 0
        it['_score'] = s + (1 if similar else 0) + affinity
    items.sort(key=lambda it: (-it['_score'], it.get(name_key, '')))
    for it in items:
        it.pop('_score', None)


@api_view(['GET'])
def search_data(request):
    """Everything the search page needs in one call: the theme list, all
    approved resources and all active guides (with their category)."""
    cats = [
        {
            'id': c.id, 'name': c.name, 'icon': c.icon,
            'subcategories': [{'id': s.id, 'name': s.name} for s in c.subcategories.all()],
        }
        for c in Category.objects.order_by('-priority', 'name').prefetch_related('subcategories')
    ]
    cat_names = {c['id']: c['name'] for c in cats}

    # Only standalone resources (those with a category). Resources that exist
    # purely as guide steps have no category and are shown inside guides.
    resources = (
        Resource.objects.filter(status=Resource.STATUS_APPROVED, category__isnull=False)
        .select_related('category', 'author', 'subcategory')
        .prefetch_related('tags', 'attachments', 'places', 'translations')
        .order_by('name')
    )
    rdata = ResourceSerializer(resources, many=True, context={'request': request}).data
    for r in rdata:
        cid = r.get('category')
        r['category'] = {'id': cid, 'name': cat_names[cid]} if cid in cat_names else None

    guides = (
        Guide.objects.filter(is_active=True).select_related('category').order_by('order')
        .prefetch_related(
            'tags',
            'steps__resource__tags', 'steps__resource__places',
            'steps__resource__attachments', 'steps__resource__translations',
            'translations',
        )
    )
    gdata = GuideSerializer(guides, many=True, context={'request': request}).data

    # Default ranking: surface the resources and guides most relevant to the
    # visitor first. Three signals combine, the editorial match (tags flagged by
    # matching audiences), similar profiles' likes, and the visitor's own saved/liked.
    profile_id = request.query_params.get('profile')
    if profile_id:
        try:
            profile = Profile.objects.get(pk=profile_id)
            tag_ids = _matched_tag_ids(profile)
            similar_likes = _similar_liked(profile)
            # Personal affinity from what the visitor liked (server-side) and
            # saved (sent by the client as ?saved=1,2,3).
            liked_ids = set(
                ResourceFeedback.objects
                .filter(profile=profile, is_useful=True)
                .values_list('resource_id', flat=True)
            )
            saved_ids = {int(s) for s in request.query_params.get('saved', '').split(',') if s.isdigit()}
            affinity_source = liked_ids | saved_ids
            affinity_tags = _affinity_tags(affinity_source)
            _rank_by_profile(rdata, 'name', profile, tag_ids,
                             similar_likes, affinity_tags, affinity_source)
            _rank_by_profile(gdata, 'title', profile, tag_ids,
                             set(), set(), set())
        except Profile.DoesNotExist:
            pass

    return Response({'categories': cats, 'resources': rdata, 'guides': gdata})


class ResourceViewSet(ModelViewSet):
    serializer_class = ResourceSerializer

    def get_queryset(self):
        qs = Resource.objects.filter(status=Resource.STATUS_APPROVED).prefetch_related(
            'tags', 'attachments', 'places', 'translations',
        ).select_related('category', 'author').order_by('name')
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


class GuideViewSet(ReadOnlyModelViewSet):
    def get_queryset(self):
        if self.action == 'retrieve':
            return Guide.objects.prefetch_related(
                'steps__resource__tags',
                'steps__resource__attachments',
                'steps__resource__places',
                'steps__resource__translations',
            ).filter(is_active=True).order_by('order')
        return Guide.objects.filter(is_active=True).order_by('order')

    def get_serializer_class(self):
        if self.action == 'list':
            return GuideBriefSerializer
        return GuideSerializer


@api_view(['POST'])
def chat_view(request):
    from django.conf import settings as django_settings
    import urllib.request
    import urllib.error
    import json as json_lib

    api_key = django_settings.INFOMANIAK_API_KEY
    product_id = django_settings.INFOMANIAK_PRODUCT_ID
    model = django_settings.INFOMANIAK_MODEL

    if not api_key or not product_id:
        return Response({'error': 'AI not configured — set INFOMANIAK_API_KEY and INFOMANIAK_PRODUCT_ID in backend/.env'}, status=503)

    user_message = request.data.get('message', '').strip()
    history = request.data.get('history', [])

    if not user_message:
        return Response({'error': 'Message required'}, status=400)

    all_resources = Resource.objects.filter(status=Resource.STATUS_APPROVED).prefetch_related('tags').select_related('category')

    catalog_lines = []
    for r in all_resources:
        tags = ', '.join(t.label for t in r.tags.all())
        cat_name = r.category.name if r.category else "Parcours"
        line = f"[ID={r.id}][{cat_name}] {r.name}"
        if r.description:
            line += f" — {r.description}"
        if tags:
            line += f" (tags: {tags})"
        catalog_lines.append(line)

    catalog = '\n'.join(catalog_lines) if catalog_lines else '(no resources yet)'

    guide_lines = []
    for gd in Guide.objects.filter(is_active=True).select_related('category'):
        cat_name = gd.category.name if gd.category else 'Guide'
        line = f"[GD={gd.id}][{cat_name}] {gd.title}"
        if gd.description:
            line += f" — {gd.description}"
        guide_lines.append(line)
    guides_catalog = '\n'.join(guide_lines) if guide_lines else '(no guides yet)'

    system_prompt = f"""You are a helpful assistant for newcomers (migrants) living in Switzerland.
Your job is to recommend relevant resources and step-by-step guides from the lists below.

AVAILABLE RESOURCES (each starts with its ID):
{catalog}

AVAILABLE GUIDES (step-by-step guides, each starts with its GD id):
{guides_catalog}

RULES:
- Respond ONLY with valid JSON, no other text, no markdown code block.
- Format: {{"message": "Your short explanation here.", "resource_ids": [id1, id2], "guide_ids": [gd1]}}
- Recommend 1 to 3 items total (resources and/or guides). Use the exact integer IDs.
- Prefer a guide when the user needs a full step-by-step process.
- The message must be short, simple sentences (FALC style).
- Reply in the same language the user writes in.
- If nothing matches, return: {{"message": "I could not find a matching resource.", "resource_ids": [], "guide_ids": []}}"""

    messages = [
        {'role': 'system', 'content': system_prompt},
        *history[-6:],
        {'role': 'user', 'content': user_message},
    ]

    payload = json_lib.dumps({
        'model': model,
        'messages': messages,
        'max_tokens': 400,
        'temperature': 0.2,
    }).encode('utf-8')

    req = urllib.request.Request(
        f'https://api.infomaniak.com/2/ai/{product_id}/openai/v1/chat/completions',
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json_lib.loads(resp.read())
        raw = result['choices'][0]['message']['content'].strip()

        # Extract JSON even if the model wraps it in ```json ... ```
        import re
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        parsed = json_lib.loads(json_match.group()) if json_match else {}

        reply_text = parsed.get('message', raw)
        resource_ids = [int(i) for i in parsed.get('resource_ids', []) if str(i).isdigit()]
        guide_ids = [int(i) for i in parsed.get('guide_ids', []) if str(i).isdigit()]

        matched = Resource.objects.filter(id__in=resource_ids, status=Resource.STATUS_APPROVED).select_related('category').prefetch_related('attachments', 'places')
        resource_data = []
        for r in matched:
            attachments = []
            for a in r.attachments.all():
                file_url = a.file.url
                if not file_url.startswith('http'):
                    file_url = request.build_absolute_uri(file_url)
                attachments.append({'id': a.id, 'file': file_url, 'label': a.label, 'order': a.order})
            resource_data.append({
                'id': r.id,
                'name': r.name,
                'description': r.description,
                'sections': render_sections(r),
                'attachments': attachments,
                'category': {'id': r.category.id, 'name': r.category.name} if r.category else None,
            })

        guide_data = []
        if guide_ids:
            gds = Guide.objects.filter(id__in=guide_ids, is_active=True).prefetch_related(
                'steps__resource__tags', 'steps__resource__places', 'steps__resource__attachments',
                'steps__resource__translations',
            )
            guide_data = GuideSerializer(gds, many=True, context={'request': request}).data

        return Response({'reply': reply_text, 'resources': resource_data, 'guides': guide_data})
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return Response({'error': f'AI API error ({e.code}): {body}'}, status=502)
    except Exception as e:
        return Response({'error': str(e)}, status=502)


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

from datetime import date as date_cls
from django.db.models import Count, Prefetch
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from .models import Profile, Audience, Category, Resource, Tag, ResourceFeedback, Attachment, Pathway
from .serializers import (
    ProfileSerializer, CategorySerializer, ResourceSerializer,
    TagSerializer, ResourceFeedbackSerializer, AudienceSerializer,
    CategoryBriefSerializer, PathwayBriefSerializer, PathwaySerializer,
    render_sections,
)


def _compute_age(birth_date):
    if not birth_date:
        return None
    today = date_cls.today()
    return today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


_COMPUTER_SKILLS_ORDER = {'none': 0, 'basic': 1, 'advanced': 2}
_EDUCATION_LEVEL_ORDER = {'primary': 0, 'secondary': 1, 'vocational': 2, 'bachelor': 3, 'master_plus': 4}


def _audience_matches(audience, profile, age):
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

    if audience.min_age is not None and age is not None:
        if age < audience.min_age:
            return False

    if audience.max_age is not None and age is not None:
        if age > audience.max_age:
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
    age = _compute_age(profile.birth_date)
    tag_ids = set()
    for audience in Audience.objects.prefetch_related('relevant_tags').all():
        if _audience_matches(audience, profile, age):
            tag_ids.update(t.id for t in audience.relevant_tags.all())
    return tag_ids


COMMUNITY_MIN_LIKES = 2


def _cohort_likes_by_language(profile):
    """Returns resource_ids liked by >= COMMUNITY_MIN_LIKES profiles sharing the same language."""
    qs = (
        ResourceFeedback.objects
        .filter(is_useful=True, profile__language=profile.language)
        .exclude(profile_id=profile.pk)
        .values('resource_id')
        .annotate(n=Count('resource_id'))
    )
    return {row['resource_id'] for row in qs if row['n'] >= COMMUNITY_MIN_LIKES}


def _cohort_likes_by_status(profile):
    """Returns resource_ids liked by >= COMMUNITY_MIN_LIKES profiles sharing the same status."""
    qs = (
        ResourceFeedback.objects
        .filter(is_useful=True, profile__status=profile.status)
        .exclude(profile_id=profile.pk)
        .values('resource_id')
        .annotate(n=Count('resource_id'))
    )
    return {row['resource_id'] for row in qs if row['n'] >= COMMUNITY_MIN_LIKES}


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
            .prefetch_related('tags', 'audiences', 'attachments', 'places', 'translations')
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
                age = _compute_age(profile.birth_date)
                all_audiences = {a.id: a for a in Audience.objects.all()}

                def score(r):
                    r_tag_ids = frozenset(t['id'] for t in r.get('tags', []))
                    aid_list = r.get('audience_ids', [])
                    if not aid_list:
                        return 0, False
                    audience_matches = sum(
                        1 for aid in aid_list
                        if aid in all_audiences and _audience_matches(all_audiences[aid], profile, age)
                    )
                    if audience_matches == 0:
                        return 0, False
                    tag_overlap = len(r_tag_ids & tag_ids)
                    if tag_overlap == 0:
                        return 0, False
                    return audience_matches + tag_overlap * 0.5, tag_overlap >= 2

                scored = sorted([(r, score(r)) for r in data['resources']], key=lambda x: -x[1][0])
                lang_likes = _cohort_likes_by_language(profile)
                stat_likes = _cohort_likes_by_status(profile)
                data['resources'] = [
                    {
                        **r,
                        'is_recommended': s > 0,
                        'recommended_by_system': rec,
                        'community_by_language': profile.language if r['id'] in lang_likes else None,
                        'community_by_status': profile.status if r['id'] in stat_likes else None,
                    }
                    for r, (s, rec) in scored
                ]
            except Profile.DoesNotExist:
                data['resources'] = [{**r, 'is_recommended': False, 'recommended_by_system': False, 'community_by_language': None, 'community_by_status': None} for r in data['resources']]
        else:
            data['resources'] = [{**r, 'is_recommended': False, 'recommended_by_system': False, 'community_by_language': None, 'community_by_status': None} for r in data['resources']]

        # Pathways shown under this category (co-located with resources).
        pathways = (
            instance.pathways.filter(is_active=True).order_by('order')
            .prefetch_related(
                'steps__resource__tags', 'steps__resource__places',
                'steps__resource__attachments', 'steps__resource__translations',
            )
        )
        data['pathways'] = PathwaySerializer(pathways, many=True, context={'request': request}).data

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

    age = _compute_age(profile.birth_date)
    lang_likes = _cohort_likes_by_language(profile)
    stat_likes = _cohort_likes_by_status(profile)
    results = []
    for cat in Category.objects.prefetch_related(
        'resources__tags', 'resources__audiences', 'resources__attachments', 'resources__subcategory', 'resources__places',
    ).all():
        for resource in cat.resources.all():
            if resource.status != Resource.STATUS_APPROVED:
                continue
            resource_tag_ids = frozenset(t.id for t in resource.tags.all())
            r_audiences = list(resource.audiences.all())
            if not r_audiences:
                continue
            audience_matches = sum(1 for a in r_audiences if _audience_matches(a, profile, age))
            if audience_matches == 0:
                continue
            tag_overlap = len(resource_tag_ids & tag_ids)
            if tag_overlap == 0:
                continue
            score = audience_matches + tag_overlap * 0.5
            data = ResourceSerializer(resource, context={'request': request}).data
            results.append({
                **data,
                'score': score,
                'category': {'id': cat.id, 'name': cat.name},
                'recommended_by_system': tag_overlap >= 2,
                'community_by_language': profile.language if resource.id in lang_likes else None,
                'community_by_status': profile.status if resource.id in stat_likes else None,
            })

    results.sort(key=lambda x: -x['score'])
    return Response(results[:limit])


class ResourceViewSet(ModelViewSet):
    serializer_class = ResourceSerializer

    def get_queryset(self):
        qs = Resource.objects.filter(status=Resource.STATUS_APPROVED).prefetch_related(
            'tags', 'audiences', 'attachments', 'places', 'translations',
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


class PathwayViewSet(ReadOnlyModelViewSet):
    def get_queryset(self):
        if self.action == 'retrieve':
            return Pathway.objects.prefetch_related(
                'steps__resource__tags',
                'steps__resource__attachments',
            ).filter(is_active=True).order_by('order')
        return Pathway.objects.filter(is_active=True).order_by('order')

    def get_serializer_class(self):
        if self.action == 'list':
            return PathwayBriefSerializer
        return PathwaySerializer


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

    pathway_lines = []
    for pw in Pathway.objects.filter(is_active=True).select_related('category'):
        cat_name = pw.category.name if pw.category else 'Parcours'
        line = f"[PW={pw.id}][{cat_name}] {pw.title}"
        if pw.description:
            line += f" — {pw.description}"
        pathway_lines.append(line)
    pathways_catalog = '\n'.join(pathway_lines) if pathway_lines else '(no pathways yet)'

    system_prompt = f"""You are a helpful assistant for newcomers (migrants) living in Switzerland.
Your job is to recommend relevant resources and step-by-step pathways from the lists below.

AVAILABLE RESOURCES (each starts with its ID):
{catalog}

AVAILABLE PATHWAYS (step-by-step guides, each starts with its PW id):
{pathways_catalog}

RULES:
- Respond ONLY with valid JSON, no other text, no markdown code block.
- Format: {{"message": "Your short explanation here.", "resource_ids": [id1, id2], "pathway_ids": [pw1]}}
- Recommend 1 to 3 items total (resources and/or pathways). Use the exact integer IDs.
- Prefer a pathway when the user needs a full step-by-step process.
- The message must be short, simple sentences (FALC style).
- Reply in the same language the user writes in.
- If nothing matches, return: {{"message": "I could not find a matching resource.", "resource_ids": [], "pathway_ids": []}}"""

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
        pathway_ids = [int(i) for i in parsed.get('pathway_ids', []) if str(i).isdigit()]

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

        pathway_data = []
        if pathway_ids:
            pws = Pathway.objects.filter(id__in=pathway_ids, is_active=True).prefetch_related(
                'steps__resource__tags', 'steps__resource__places', 'steps__resource__attachments',
            )
            pathway_data = PathwaySerializer(pws, many=True, context={'request': request}).data

        return Response({'reply': reply_text, 'resources': resource_data, 'pathways': pathway_data})
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

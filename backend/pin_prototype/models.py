import json
import re
import urllib.parse
import urllib.request

from django.conf import settings
from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, PreviewableMixin


def geocode_ch(address):
    """Geocode a Swiss address to (lat, lng) using the official swisstopo
    search service. Returns None on failure (network, no result)."""
    if not address:
        return None
    # Drop parenthetical notes (e.g. "(+ permanences …)") that confuse geocoding.
    query = address.split(' (')[0].strip()
    if not query:
        return None
    try:
        url = 'https://api3.geo.admin.ch/rest/services/api/SearchServer?' + urllib.parse.urlencode({
            'type': 'locations', 'origins': 'address', 'limit': '1', 'sr': '4326',
            'searchText': query,
        })
        req = urllib.request.Request(url, headers={'User-Agent': 'pin-prototype'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            results = json.loads(resp.read()).get('results') or []
        if not results:
            return None
        attrs = results[0].get('attrs', {})
        lat, lon = attrs.get('lat'), attrs.get('lon')
        return (float(lat), float(lon)) if lat is not None and lon is not None else None
    except Exception:
        return None


class Profile(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('fr', 'Français'),
        ('uk', 'Українська'),
        ('ru', 'Русский'),
    ]

    FRENCH_LEVEL_CHOICES = [
        ('none', 'No French yet'),
        ('A1', 'A1'),
        ('A2', 'A2'),
        ('B1', 'B1'),
        ('B2', 'B2'),
        ('C1', 'C1'),
        ('C2', 'C2'),
    ]

    STATUS_CHOICES = [
        ('N', 'Permit N — Asylum seeker'),
        ('F', 'Permit F — Provisional admission'),
        ('S', 'Permit S — Protection status'),
        ('B', 'Permit B — Residence permit'),
        ('C', 'Permit C — Settlement permit'),
        ('L', 'Permit L — Short-term permit'),
        ('G', 'Permit G — Cross-border commuter'),
        ('other', 'Other'),
    ]

    COMPUTER_SKILLS_CHOICES = [
        ('none', 'No computer skills'),
        ('basic', 'Basic (internet, email)'),
        ('advanced', 'Advanced (office tools, digital)'),
    ]

    # Only higher-education levels: the platform targets an autonomous profile
    # whose qualifications are likelier to be recognised (see report §5.2).
    EDUCATION_LEVEL_CHOICES = [
        ('vocational', 'Vocational training (CFC/AFP)'),
        ('bachelor', 'University (Bachelor or equivalent)'),
        ('master_plus', 'Master, Doctorate or higher'),
    ]

    # Field the person studied or worked in back home — paired with the
    # education question to refine similar-profile recommendations.
    ORIGIN_SECTOR_CHOICES = [
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('engineering', 'Engineering'),
        ('trade', 'Trade & commerce'),
        ('agriculture', 'Agriculture'),
        ('construction', 'Construction'),
        ('it', 'IT & technology'),
        ('arts', 'Arts & culture'),
        ('administration', 'Administration'),
        ('catering', 'Catering & food'),
        ('transport', 'Transport'),
        ('other', 'Other'),
    ]

    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES)
    french_level = models.CharField(max_length=5, choices=FRENCH_LEVEL_CHOICES, blank=True, default='none')
    status = models.CharField(max_length=5, choices=STATUS_CHOICES, default='other')
    has_children = models.BooleanField(null=True, blank=True)
    arrived_over_year_ago = models.BooleanField(null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    has_driving_license = models.BooleanField(null=True, blank=True)
    computer_skills = models.CharField(max_length=10, choices=COMPUTER_SKILLS_CHOICES, blank=True, default='none')
    education_level = models.CharField(max_length=15, choices=EDUCATION_LEVEL_CHOICES, blank=True, default='')
    origin_sector = models.CharField(max_length=20, choices=ORIGIN_SECTOR_CHOICES, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile #{self.pk} — {self.get_language_display()}"


class Audience(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    statuses = models.CharField(max_length=50, blank=True, help_text="Comma-separated permit codes, e.g. N,F,S. Empty = any.")
    has_children = models.BooleanField(null=True, blank=True, help_text="True/False to filter, leave blank for any.")
    arrived_over_year = models.BooleanField(null=True, blank=True, help_text="True/False to filter, leave blank for any.")
    has_driving_license = models.BooleanField(null=True, blank=True, help_text="If set, profile must match.")
    min_computer_skills = models.CharField(max_length=10, blank=True, choices=[('basic', 'Basic'), ('advanced', 'Advanced')], help_text="Minimum computer skill level. Empty = any.")
    min_education_level = models.CharField(max_length=15, blank=True, choices=[('primary', 'Primary'), ('secondary', 'Secondary'), ('vocational', 'Vocational'), ('bachelor', 'Bachelor'), ('master_plus', 'Master+')], help_text="Minimum education level. Empty = any.")
    relevant_tags = models.ManyToManyField('Tag', blank=True, related_name='audiences', help_text="Resources with these tags are shown first when this audience matches.")

    def __str__(self):
        return self.name


class Category(ClusterableModel):
    ICON_CHOICES = [
        ('CurrencyDollarIcon', 'Money & Budget'),
        ('BriefcaseIcon', 'Work'),
        ('AcademicCapIcon', 'Education'),
        ('HomeIcon', 'Housing'),
        ('HeartIcon', 'Health'),
        ('UsersIcon', 'Family'),
        ('TruckIcon', 'Mobility'),
        ('ScaleIcon', 'Rights & Duties'),
        ('HandRaisedIcon', 'Help'),
        ('GlobeAltIcon', 'Global / International'),
        ('DocumentTextIcon', 'Documents'),
        ('BuildingOfficeIcon', 'Administration'),
        ('PhoneIcon', 'Contact'),
        ('MapPinIcon', 'Location'),
        ('ComputerDesktopIcon', 'Technology'),
        ('ShieldCheckIcon', 'Security'),
        ('ChatBubbleLeftIcon', 'Communication'),
        ('StarIcon', 'Other'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, choices=ICON_CHOICES)
    audiences = models.ManyToManyField(Audience, blank=True, related_name='categories', help_text="Leave empty to show to everyone.")
    priority = models.IntegerField(default=0, help_text="Higher = shown first.")

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    category = ParentalKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'subcategories'

    def __str__(self):
        return f"{self.category.name} › {self.name}"


class Tag(models.Model):
    label = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.label


class Contributor(models.Model):
    """An organisation that can author resources (COSM by default, or a guest
    organisation such as Caritas). Guest users are linked here via `editors`."""
    name = models.CharField(max_length=100, unique=True)
    is_default = models.BooleanField(default=False, help_text='The default author (COSM). Keep only one.')
    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='contributor_orgs',
        help_text='Guest users who write on behalf of this organisation.',
    )

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return self.name

    @classmethod
    def get_default(cls):
        return cls.objects.filter(is_default=True).first() or cls.objects.first()


_RICHTEXT_FEATURES = ['h1', 'h2', 'h3', 'bold', 'italic', 'link', 'document-link', 'ol', 'ul', 'blockquote', 'hr', 'image', 'embed']


class SectionBlock(blocks.StructBlock):
    """One titled section of a resource body. The three standard kinds (why /
    how / location) keep their UI-translated titles on the frontend; a 'custom'
    section uses its own heading. This block replaces the former fixed
    why_interesting / how_to / location fields while keeping the exact same
    on-screen rendering — the editor can now add, remove or reorder sections."""
    kind = blocks.ChoiceBlock(
        choices=[
            ('why', 'Why is it interesting?'),
            ('how', 'How to do it?'),
            ('location', 'Location'),
            ('custom', 'Custom section'),
        ],
        default='custom',
    )
    heading = blocks.CharBlock(
        required=False,
        help_text='Title shown for a custom section (ignored for the three standard kinds).',
    )
    content = blocks.RichTextBlock(features=_RICHTEXT_FEATURES)

    class Meta:
        icon = 'doc-full'
        label = 'Section'


class Resource(PreviewableMixin, ClusterableModel):
    preview_modes = [('default', 'Mobile preview')]

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending review'),
        (STATUS_APPROVED, 'Approved'),
    ]

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='resources', null=True, blank=True)
    subcategory = models.ForeignKey(
        Subcategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resources',
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='resources')
    name = models.CharField(max_length=200)
    # Sections fixes (même template pour chaque ressource) — inspiré de refugies.info
    description = models.TextField(blank=True, help_text='Short intro shown at the top.')
    # Body as a flexible list of titled sections (StreamField → one JSON column).
    # Replaces the three fixed fields below, which are kept for the transition and
    # as a fallback; they can be dropped once everything reads from `body`.
    body = StreamField([('section', SectionBlock())], blank=True, verbose_name='Body (sections)')
    why_interesting = RichTextField(blank=True, features=_RICHTEXT_FEATURES, verbose_name='Why is it interesting? (legacy)')
    how_to = RichTextField(blank=True, features=_RICHTEXT_FEATURES, verbose_name='How to do it? (legacy)')
    location = RichTextField(blank=True, features=_RICHTEXT_FEATURES, verbose_name='Location (legacy)')
    author = models.ForeignKey(
        Contributor, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources',
        help_text='Organisation that wrote this resource. Defaults to COSM.',
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_APPROVED,
        help_text='Guest-written resources start pending and must be approved by COSM before appearing in the app.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def get_preview_template(self, request, mode_name):
        return 'pin_prototype/resource_preview.html'

    def get_preview_context(self, request, mode_name):
        return {
            'title': self.name,
            'description': self.description,
            'category': self.category.name if self.category_id else None,
            'author': self.author.name if self.author_id else 'COSM',
            'sections': preview_sections(resource_section_dicts(self)),
        }

    def admin_kind(self):
        """Distinguish standalone fiches (first-person titles) from guide steps
        (action titles) in the Wagtail list, so the mix isn't confusing."""
        return 'Étape de guide' if self.guide_steps.exists() else 'Fiche'
    admin_kind.short_description = 'Type'

    def __str__(self):
        return self.name


def section_stream_blocks(why, how, location):
    """Build StreamField section blocks from the three legacy section values.
    Shared by the data migration and the seed so `body` stays in sync."""
    out = []
    for kind, html in (('why', why), ('how', how), ('location', location)):
        if html and str(html).strip():
            out.append(('section', {'kind': kind, 'heading': '', 'content': str(html)}))
    return out


def resource_section_dicts(resource):
    """Plain dicts {kind, heading, content} from a resource's body StreamField,
    falling back to the legacy why/how/location fields when the body is empty.
    The single source of truth for both API rendering and translation."""
    out = []
    body = getattr(resource, 'body', None)
    if body:
        for block in body:
            if block.block_type != 'section':
                continue
            value = block.value
            content = value.get('content')
            source = content.source if hasattr(content, 'source') else str(content or '')
            out.append({
                'kind': value.get('kind') or 'custom',
                'heading': value.get('heading') or '',
                'content': source,
            })
    if out:
        return out
    # Legacy fallback (Resource only; translations have no such fields).
    for kind, html in (
        ('why', getattr(resource, 'why_interesting', '')),
        ('how', getattr(resource, 'how_to', '')),
        ('location', getattr(resource, 'location', '')),
    ):
        if html and str(html).strip():
            out.append({'kind': kind, 'heading': '', 'content': str(html)})
    return out


# --- Admin preview helpers -------------------------------------------------
# These power the Wagtail preview only. They give it a clean, self-contained
# look (split each section into collapsible items, French section titles) and
# are deliberately NOT coupled to the Vue app's styling.

_PREVIEW_SECTION_TITLES = {
    'why': "Pourquoi c'est intéressant ?",
    'how': 'Comment faire ?',
    'location': 'Lieu',
}

_HEADING_RE = re.compile(r'(<h[1-3][^>]*>.*?</h[1-3]>)', re.IGNORECASE | re.DOTALL)


def _split_section_html(html):
    """Split a section's HTML into an intro (before the first heading) and
    collapsible items (heading + the content that follows), like the app does."""
    intro, items, current = '', [], None
    for part in _HEADING_RE.split(html or ''):
        if not part:
            continue
        m = re.match(r'<h[1-3][^>]*>(.*?)</h[1-3]>', part, re.IGNORECASE | re.DOTALL)
        if m:
            current = {'title': re.sub(r'<[^>]+>', '', m.group(1)).strip(), 'html': ''}
            items.append(current)
        elif current is None:
            intro += part
        else:
            current['html'] += part
    return {'intro': intro.strip(), 'items': items}


def preview_sections(section_dicts):
    """Preview-ready sections: French title + intro + collapsible items."""
    from wagtail.rich_text import expand_db_html
    out = []
    for d in section_dicts:
        html = expand_db_html(d.get('content') or '')
        if not html.strip():
            continue
        split = _split_section_html(html)
        kind = d.get('kind') or 'custom'
        out.append({
            'title': _PREVIEW_SECTION_TITLES.get(kind, d.get('heading') or ''),
            'intro': split['intro'],
            'items': split['items'],
        })
    return out


class ResourcePlace(Orderable):
    """A map location shown in a resource's 'Location' section. The editor only
    enters a name and an address; coordinates are geocoded automatically."""
    resource = ParentalKey(Resource, on_delete=models.CASCADE, related_name='places')
    name = models.CharField(max_length=200, help_text='Name of the place, e.g. "COSM Neuchâtel".')
    city = models.CharField(max_length=120, blank=True, help_text='City, shown under the name.')
    address = models.CharField(max_length=300, blank=True, help_text='Full address. The map location is found automatically.')
    phone = models.CharField(max_length=50, blank=True)
    email = models.CharField(max_length=120, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # The editor fills these; coordinates are geocoded from the address on save.
    panels = [
        FieldPanel('name'),
        FieldPanel('city'),
        FieldPanel('address'),
        FieldPanel('phone'),
        FieldPanel('email'),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_address = self.address

    def save(self, *args, geocode=True, **kwargs):
        # Geocode when coordinates are missing or the address changed.
        if geocode and self.address and (self.latitude is None or self.longitude is None or self.address != self.__original_address):
            coords = geocode_ch(self.address)
            if coords:
                self.latitude, self.longitude = coords
        super().save(*args, **kwargs)
        self.__original_address = self.address

    def __str__(self):
        return self.name


class Attachment(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='attachments')
    order = models.IntegerField(default=0)
    file = models.FileField(upload_to='resources/')
    label = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.label or self.file.name


class ResourceTranslation(PreviewableMixin, models.Model):
    """A machine translation of a resource's text into another language.
    HTML sections are stored as-is. The base content (French) stays on Resource."""
    preview_modes = [('default', 'Mobile preview')]

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending review'),
        (STATUS_APPROVED, 'Approved'),
    ]

    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=5)
    name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    # Translated body — same section structure as the resource, so it edits as
    # rich-text blocks in Wagtail (not a raw JSON blob) and previews identically.
    body = StreamField([('section', SectionBlock())], blank=True, verbose_name='Body (sections)')
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_APPROVED,
        help_text='Only approved translations appear in the app. AI translations are set to pending for review.',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['resource', 'language']]

    def __str__(self):
        return f"{self.resource} [{self.language}]"

    def get_preview_template(self, request, mode_name):
        return 'pin_prototype/resource_preview.html'

    def get_preview_context(self, request, mode_name):
        # Same phone layout as the resource: feed the template normalized
        # sections from the translated body, falling back to the resource's.
        dicts = resource_section_dicts(self)
        if not dicts and self.resource_id:
            dicts = resource_section_dicts(self.resource)
        res = self.resource if self.resource_id else None
        return {
            'title': self.name or (res.name if res else ''),
            'description': self.description or (res.description if res else ''),
            'category': res.category.name if (res and res.category_id) else None,
            'author': (res.author.name if (res and res.author_id) else 'COSM'),
            'sections': preview_sections(dicts),
        }


class Guide(PreviewableMixin, ClusterableModel):
    preview_modes = [('default', 'Mobile preview')]

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, related_name='guides', null=True, blank=True,
        help_text='Category this guide is shown under.',
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='guides')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

    def get_preview_template(self, request, mode_name):
        return 'pin_prototype/guide_preview.html'

    def get_preview_context(self, request, mode_name):
        steps = []
        for i, step in enumerate(self.steps.all(), start=1):
            res = step.resource
            steps.append({
                'num': i,
                'title': step.step_label or (res.name if res else ''),
                'description': (res.description if res else ''),
                'sections': preview_sections(resource_section_dicts(res)) if res else [],
            })
        return {
            'title': self.title,
            'description': self.description,
            'category': self.category.name if self.category_id else None,
            'step_count': len(steps),
            'steps': steps,
        }


class GuideStep(Orderable):
    # A step IS a resource (reusable, recommended, translatable). It is edited
    # inline inside its guide via the resource chooser below.
    guide = ParentalKey(Guide, related_name='steps', on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='guide_steps')
    step_label = models.CharField(max_length=200, blank=True, help_text='Optional step title. Defaults to the resource name.')

    panels = [
        FieldPanel('resource'),
        FieldPanel('step_label'),
    ]

    def __str__(self):
        label = self.step_label or (self.resource.name if self.resource_id else '')
        return f"{self.guide.title} › {label}"


class GuideTranslation(models.Model):
    """Translation of a guide's own title/description. The steps translate via
    their resources (ResourceTranslation); this only covers the guide-level text."""
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending review'),
        (STATUS_APPROVED, 'Approved'),
    ]

    guide = models.ForeignKey(Guide, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=5)
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_APPROVED)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['guide', 'language']]

    def __str__(self):
        return f"{self.guide} [{self.language}]"


class ResourceFeedback(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='feedbacks')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='feedbacks')
    is_useful = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['profile', 'resource']]

    def __str__(self):
        mark = '✓' if self.is_useful else '✗'
        return f"{mark} profile#{self.profile_id} → {self.resource}"

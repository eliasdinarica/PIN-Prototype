import json
import urllib.parse
import urllib.request

from django.conf import settings
from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
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
        ('de', 'Deutsch'),
        ('it', 'Italiano'),
        ('es', 'Español'),
        ('pt', 'Português'),
        ('ru', 'Русский'),
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

    EDUCATION_LEVEL_CHOICES = [
        ('primary', 'Primary school or less'),
        ('secondary', 'Secondary school (mandatory)'),
        ('vocational', 'Vocational training (CFC/AFP)'),
        ('bachelor', 'University (Bachelor or equivalent)'),
        ('master_plus', 'Master, Doctorate or higher'),
    ]

    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES)
    other_languages = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=5, choices=STATUS_CHOICES, default='other')
    has_children = models.BooleanField(null=True, blank=True)
    arrived_over_year_ago = models.BooleanField(null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    has_driving_license = models.BooleanField(null=True, blank=True)
    computer_skills = models.CharField(max_length=10, choices=COMPUTER_SKILLS_CHOICES, blank=True, default='none')
    education_level = models.CharField(max_length=15, choices=EDUCATION_LEVEL_CHOICES, blank=True, default='primary')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile #{self.pk} — {self.get_language_display()}"


class Audience(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    statuses = models.CharField(max_length=50, blank=True, help_text="Comma-separated permit codes, e.g. N,F,S. Empty = any.")
    has_children = models.BooleanField(null=True, blank=True, help_text="True/False to filter, leave blank for any.")
    arrived_over_year = models.BooleanField(null=True, blank=True, help_text="True/False to filter, leave blank for any.")
    min_age = models.IntegerField(null=True, blank=True)
    max_age = models.IntegerField(null=True, blank=True)
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
    audiences = models.ManyToManyField(Audience, blank=True, related_name='resources')
    tags = models.ManyToManyField(Tag, blank=True, related_name='resources')
    name = models.CharField(max_length=200)
    # Sections fixes (même template pour chaque ressource) — inspiré de refugies.info
    description = models.TextField(blank=True, help_text='Short intro shown at the top.')
    why_interesting = RichTextField(blank=True, features=_RICHTEXT_FEATURES, verbose_name='Why is it interesting?')
    how_to = RichTextField(blank=True, features=_RICHTEXT_FEATURES, verbose_name='How to do it?')
    location = RichTextField(blank=True, features=_RICHTEXT_FEATURES, verbose_name='Location')
    author = models.ForeignKey(
        Contributor, on_delete=models.SET_NULL, null=True, blank=True, related_name='resources',
        help_text='Organisation that wrote this resource. Defaults to COSM.',
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_APPROVED,
        help_text='Guest-written resources start pending and must be approved by COSM before appearing in the app.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def author_name(self):
        return self.author.name if self.author else 'COSM'

    def get_preview_template(self, request, mode_name):
        return 'pin_prototype/resource_preview.html'

    def get_preview_context(self, request, mode_name):
        return {'resource': self}

    def __str__(self):
        return self.name


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


class ResourceTranslation(models.Model):
    """A machine translation of a resource's text into another language.
    HTML sections are stored as-is. The base content (French) stays on Resource."""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=5)
    name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    why_interesting = models.TextField(blank=True)
    how_to = models.TextField(blank=True)
    location = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['resource', 'language']]

    def __str__(self):
        return f"{self.resource} [{self.language}]"


class Guide(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, related_name='guides', null=True, blank=True,
        help_text='Category this guide is shown under.',
    )
    audiences = models.ManyToManyField(Audience, blank=True, related_name='guides')
    tags = models.ManyToManyField(Tag, blank=True, related_name='guides')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class GuideStep(models.Model):
    guide = models.ForeignKey(Guide, related_name='steps', on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='guide_steps')
    order = models.IntegerField(default=0)
    step_label = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.guide.title} › étape {self.order}"


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

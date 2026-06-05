from django.db import models
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.models import PreviewableMixin


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


class Category(models.Model):
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
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
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


_RICHTEXT_FEATURES = ['h2', 'h3', 'bold', 'italic', 'link', 'ol', 'ul', 'blockquote', 'hr', 'image', 'embed']
_RICHTEXT_FEATURES_SIMPLE = ['h2', 'h3', 'bold', 'italic', 'link', 'ol', 'ul', 'blockquote']


class Resource(PreviewableMixin, models.Model):
    preview_modes = [('default', 'Mobile preview')]
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='resources', null=True, blank=True)
    subcategory = models.ForeignKey(
        Subcategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resources',
    )
    audiences = models.ManyToManyField(Audience, blank=True, related_name='resources')
    tags = models.ManyToManyField(Tag, blank=True, related_name='resources')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    body = StreamField([
        ('richtext', blocks.RichTextBlock(
            features=_RICHTEXT_FEATURES,
            label='Rich text',
        )),
        ('image', ImageChooserBlock(label='Image')),
        ('embed', EmbedBlock(label='Video / embed')),
        ('columns', blocks.StructBlock([
            ('left', blocks.RichTextBlock(features=_RICHTEXT_FEATURES_SIMPLE, label='Left column')),
            ('right', blocks.RichTextBlock(features=_RICHTEXT_FEATURES_SIMPLE, label='Right column')),
        ], label='Two columns')),
        ('callout', blocks.StructBlock([
            ('text', blocks.RichTextBlock(features=['bold', 'italic', 'link', 'ul'], label='Callout text')),
        ], label='Callout box')),
    ], use_json_field=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_preview_template(self, request, mode_name):
        return 'pin_prototype/resource_preview.html'

    def get_preview_context(self, request, mode_name):
        return {'resource': self}

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


class Pathway(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class PathwayStep(models.Model):
    pathway = models.ForeignKey(Pathway, related_name='steps', on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='pathway_steps')
    order = models.IntegerField(default=0)
    step_label = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.pathway.title} › étape {self.order}"


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

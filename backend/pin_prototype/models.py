from django.db import models


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

    ORIGIN_SECTOR_CHOICES = [
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('engineering', 'Engineering & Technical'),
        ('trade', 'Trade & Commerce'),
        ('agriculture', 'Agriculture'),
        ('construction', 'Construction'),
        ('it', 'IT & Technology'),
        ('arts', 'Arts & Culture'),
        ('administration', 'Administration'),
        ('catering', 'Catering & Food Service'),
        ('transport', 'Transport & Logistics'),
        ('other', 'Other'),
    ]

    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES)
    other_languages = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=5, choices=STATUS_CHOICES, default='other')
    has_children = models.BooleanField()
    origin_sector = models.CharField(max_length=20, choices=ORIGIN_SECTOR_CHOICES, blank=True)
    arrived_over_year_ago = models.BooleanField(null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile #{self.pk} — {self.get_language_display()}"


class Audience(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    statuses = models.CharField(max_length=50, blank=True, help_text="Comma-separated permit codes, e.g. N,F,S. Empty = any.")
    has_children = models.BooleanField(null=True, blank=True, help_text="True/False to filter, leave blank for any.")
    origin_sectors = models.CharField(max_length=200, blank=True, help_text="Comma-separated sectors, e.g. healthcare,education. Empty = any.")
    arrived_over_year = models.BooleanField(null=True, blank=True, help_text="True/False to filter, leave blank for any.")
    min_age = models.IntegerField(null=True, blank=True)
    max_age = models.IntegerField(null=True, blank=True)
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
    priority = models.IntegerField(default=0, help_text="Higher = shown first when relevance is equal.")

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Tag(models.Model):
    label = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.label


class Resource(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='resources')
    tags = models.ManyToManyField(Tag, blank=True, related_name='resources')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='resources/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

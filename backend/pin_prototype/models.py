from django.db import models


class Profile(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('fr', 'Français'),
        ('es', 'Español'),
        ('ar', 'العربية'),
        ('pt', 'Português'),
        ('zh', '中文'),
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

    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES)
    status = models.CharField(max_length=5, choices=STATUS_CHOICES, default='other')
    has_children = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile #{self.pk} — {self.get_language_display()}"


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    emoji = models.CharField(max_length=10, blank=True)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Resource(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='resources')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='resources/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

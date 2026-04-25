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

    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES)
    has_children = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile #{self.pk} — {self.get_language_display()}"

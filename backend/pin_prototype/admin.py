from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'language', 'has_children', 'created_at']
    list_filter = ['language', 'has_children']
    readonly_fields = ['created_at']

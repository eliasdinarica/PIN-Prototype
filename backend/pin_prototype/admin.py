from django.contrib import admin
from .models import Profile, Category, Resource


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'language', 'status', 'has_children', 'created_at']
    list_filter = ['language', 'status', 'has_children']
    readonly_fields = ['created_at']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'emoji', 'name', 'description']


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'created_at']
    list_filter = ['category']
    readonly_fields = ['created_at']

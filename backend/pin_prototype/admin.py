from django.contrib import admin
from .models import Profile, Category, Resource, Tag


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'language', 'status', 'has_children', 'origin_sector', 'arrived_over_year_ago', 'birth_date', 'created_at']
    list_filter = ['language', 'status', 'has_children', 'origin_sector', 'arrived_over_year_ago']
    readonly_fields = ['created_at']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'label']
    search_fields = ['label']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'icon', 'name', 'description']



@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'created_at']
    list_filter = ['category', 'tags']
    filter_horizontal = ['tags']
    readonly_fields = ['created_at']

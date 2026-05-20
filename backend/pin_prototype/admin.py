from django.contrib import admin
from .models import Profile, Audience, Category, Resource, Tag, ResourceFeedback, Attachment


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'language', 'status', 'has_children', 'origin_sector', 'arrived_over_year_ago', 'birth_date', 'created_at']
    list_filter = ['language', 'status', 'has_children', 'origin_sector', 'arrived_over_year_ago']
    readonly_fields = ['created_at']


@admin.register(Audience)
class AudienceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'statuses', 'has_children', 'origin_sectors', 'arrived_over_year', 'min_age', 'max_age']
    search_fields = ['name']
    filter_horizontal = ['relevant_tags']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'label']
    search_fields = ['label']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'icon', 'name', 'priority']
    filter_horizontal = ['audiences']


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    fields = ['order', 'file', 'label']


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'created_at']
    list_filter = ['category', 'tags', 'audiences']
    filter_horizontal = ['tags', 'audiences']
    readonly_fields = ['created_at']
    inlines = [AttachmentInline]


@admin.register(ResourceFeedback)
class ResourceFeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'profile', 'resource', 'is_useful', 'created_at']
    list_filter = ['is_useful']
    readonly_fields = ['created_at', 'updated_at']

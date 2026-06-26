from django.contrib import admin
from .models import Profile, Audience, Category, Subcategory, Resource, Tag, ResourceFeedback, Attachment


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'language', 'french_level', 'status', 'has_children', 'arrived_over_year_ago', 'has_driving_license', 'computer_skills', 'education_level', 'origin_sector', 'created_at']
    list_filter = ['language', 'french_level', 'status', 'has_children', 'arrived_over_year_ago', 'has_driving_license', 'computer_skills', 'education_level', 'origin_sector']
    readonly_fields = ['created_at']


@admin.register(Audience)
class AudienceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'statuses', 'has_children', 'arrived_over_year', 'has_driving_license', 'min_computer_skills', 'min_education_level']
    search_fields = ['name']
    filter_horizontal = ['relevant_tags']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'label']
    search_fields = ['label']


class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 0
    fields = ['name', 'order']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'icon', 'name', 'priority']
    filter_horizontal = ['audiences']
    inlines = [SubcategoryInline]


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'category', 'name', 'order']
    list_filter = ['category']
    search_fields = ['name']


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

from django.urls import reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.snippets.bulk_actions.snippet_bulk_action import SnippetBulkAction
from wagtail.admin.panels import (
    FieldPanel, InlinePanel, TabbedInterface, ObjectList,
    MultiFieldPanel, FieldRowPanel, HelpPanel,
)
from .models import Resource, Guide, Contributor, Audience, Category, Tag, ResourceTranslation


class ResourceSnippetViewSet(SnippetViewSet):
    model = Resource
    icon = 'doc-full'
    menu_label = 'Resources'
    menu_order = 100
    list_display = ['name', 'category', 'author', 'status', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['status', 'author', 'category']

    def get_queryset(self, request):
        # Hide guide-step resources (no category) — they are edited inside their
        # guide, not as standalone fiches.
        return Resource.objects.filter(category__isnull=False)

    content_panels = [
        FieldPanel('name'),
        FieldPanel('description'),
        FieldPanel('body'),
        InlinePanel('places', label='Map locations', heading='Map locations'),
    ]

    meta_panels = [
        FieldPanel('author'),
        FieldPanel('status'),
        FieldPanel('category'),
        FieldPanel('subcategory'),
        FieldPanel('audiences'),
        FieldPanel('tags'),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading='Content'),
        ObjectList(meta_panels, heading='Settings'),
    ])


class ResourceTranslationSnippetViewSet(SnippetViewSet):
    model = ResourceTranslation
    icon = 'globe'
    menu_label = 'Translations'
    menu_order = 120
    list_display = ['resource', 'language', 'status', 'updated_at']
    list_filter = ['status', 'language']
    search_fields = ['resource__name', 'name']

    def get_queryset(self, request):
        # Only standalone-fiche translations are validated here; guide-step
        # translations are handled with their guide.
        return ResourceTranslation.objects.filter(resource__category__isnull=False)

    panels = [
        HelpPanel(content=(
            '<p>Machine translations produced by the translation script. Review '
            'the text, then set the status to <b>Approved</b> so it appears in '
            'the app. Pending translations are not shown to users (they fall back '
            'to the French content).</p>'
        )),
        FieldPanel('resource', read_only=True),
        FieldPanel('language', read_only=True),
        FieldPanel('status'),
        FieldPanel('name'),
        FieldPanel('description'),
        FieldPanel('body'),
    ]


class ContributorSnippetViewSet(SnippetViewSet):
    model = Contributor
    icon = 'group'
    menu_label = 'Contributors'
    menu_order = 300
    list_display = ['name', 'is_default']
    search_fields = ['name']

    panels = [
        FieldPanel('name'),
        FieldPanel('is_default'),
        FieldPanel('editors'),
    ]


class GuideSnippetViewSet(SnippetViewSet):
    model = Guide
    icon = 'list-ul'
    menu_label = 'Guides'
    menu_order = 200
    list_display = ['title', 'order', 'is_active']
    search_fields = ['title']

    panels = [
        FieldPanel('title'),
        FieldPanel('description'),
        InlinePanel('steps', label='Step', heading='Guide steps'),
        FieldPanel('category'),
        FieldPanel('order'),
        FieldPanel('is_active'),
        FieldPanel('audiences'),
        FieldPanel('tags'),
    ]


class AudienceSnippetViewSet(SnippetViewSet):
    model = Audience
    icon = 'group'
    menu_label = 'Audiences'
    menu_order = 250
    list_display = [
        'name', 'statuses', 'has_children', 'arrived_over_year',
        'min_computer_skills', 'min_education_level',
    ]
    list_filter = [
        'has_children', 'arrived_over_year', 'has_driving_license',
        'min_computer_skills', 'min_education_level',
    ]
    search_fields = ['name', 'description']

    panels = [
        HelpPanel(content=(
            '<p>An <b>audience</b> describes a group of people through a set of '
            'conditions. A profile that matches <b>all</b> the filled conditions '
            'below will see the resources carrying the chosen tags pushed to the '
            'top of its recommendations.</p>'
            '<p>Leave a field empty to ignore that criterion.</p>'
        )),
        MultiFieldPanel(
            [
                FieldPanel('name'),
                FieldPanel('description'),
            ],
            heading='Identity',
        ),
        MultiFieldPanel(
            [
                FieldPanel('statuses'),
                FieldRowPanel([
                    FieldPanel('has_children'),
                    FieldPanel('arrived_over_year'),
                ]),
                FieldPanel('has_driving_license'),
                FieldRowPanel([
                    FieldPanel('min_computer_skills'),
                    FieldPanel('min_education_level'),
                ]),
            ],
            heading='Matching criteria',
        ),
        MultiFieldPanel(
            [FieldPanel('relevant_tags')],
            heading='Resources to highlight',
        ),
    ]


class CategorySnippetViewSet(SnippetViewSet):
    model = Category
    icon = 'folder-open-inverse'
    menu_label = 'Categories'
    menu_order = 220
    list_display = ['name', 'icon', 'priority']
    search_fields = ['name', 'description']

    panels = [
        FieldPanel('name'),
        FieldPanel('description'),
        FieldPanel('icon'),
        FieldPanel('priority'),
        FieldPanel('audiences'),
        InlinePanel('subcategories', label='Subcategories', heading='Subcategories'),
    ]


class TagSnippetViewSet(SnippetViewSet):
    model = Tag
    icon = 'tag'
    menu_label = 'Tags'
    menu_order = 310
    list_display = ['label']
    search_fields = ['label']

    panels = [
        FieldPanel('label'),
    ]


register_snippet(ResourceSnippetViewSet)
register_snippet(ResourceTranslationSnippetViewSet)
register_snippet(ContributorSnippetViewSet)
register_snippet(GuideSnippetViewSet)
register_snippet(AudienceSnippetViewSet)
register_snippet(CategorySnippetViewSet)
register_snippet(TagSnippetViewSet)


# --- Guest workflow enforcement -------------------------------------------

def _user_contributor(user):
    """The organisation a guest user writes for (None for COSM admins)."""
    return user.contributor_orgs.first()


def _enforce_resource_rules(request, instance):
    if not isinstance(instance, Resource):
        return
    user = request.user
    changed = False

    # Only COSM admins (superusers) may approve. Anything a guest creates or
    # edits goes (back) to pending review, attributed to their organisation.
    if not user.is_superuser:
        if instance.status != Resource.STATUS_PENDING:
            instance.status = Resource.STATUS_PENDING
            changed = True
        org = _user_contributor(user)
        if org and instance.author_id != org.id:
            instance.author = org
            changed = True

    if instance.author_id is None:
        default = Contributor.get_default()
        if default:
            instance.author = default
            changed = True

    if changed:
        instance.save()


@hooks.register('after_create_snippet')
def _resource_after_create(request, instance):
    _enforce_resource_rules(request, instance)


@hooks.register('after_edit_snippet')
def _resource_after_edit(request, instance):
    _enforce_resource_rules(request, instance)


@hooks.register('register_admin_menu_item')
def register_validate_menu_item():
    url = reverse('wagtailsnippets_pin_prototype_resource:list') + '?status=pending'
    return MenuItem('To validate', url, icon_name='check', order=110)


@hooks.register('register_admin_menu_item')
def register_validate_translations_menu_item():
    url = reverse('wagtailsnippets_pin_prototype_resourcetranslation:list') + '?status=pending'
    return MenuItem('Translations to validate', url, icon_name='globe', order=121)


# --- One-click validation of translations ---------------------------------

class ApproveTranslationBulkAction(SnippetBulkAction):
    """Adds an "Approve" button to the translations list: select the reviewed
    translations and approve them in one click (vs. editing the status field)."""
    display_name = 'Approve'
    action_type = 'approve'
    aria_label = 'Approve selected translations'
    template_name = 'pin_prototype/bulk_actions/confirm_approve.html'
    models = [ResourceTranslation]
    action_priority = 10

    @classmethod
    def execute_action(cls, objects, **kwargs):
        approved = 0
        for obj in objects:
            if obj.status != ResourceTranslation.STATUS_APPROVED:
                obj.status = ResourceTranslation.STATUS_APPROVED
                obj.save(update_fields=['status'])
                approved += 1
        return approved, 0

    def get_success_message(self, num_parent_objects, num_child_objects):
        return f'{num_parent_objects} translation(s) approved.'


hooks.register('register_bulk_action', ApproveTranslationBulkAction)

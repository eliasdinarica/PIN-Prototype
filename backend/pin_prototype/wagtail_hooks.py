from django.urls import reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.admin.panels import FieldPanel, InlinePanel, TabbedInterface, ObjectList
from .models import Resource, Pathway, Contributor


class ResourceSnippetViewSet(SnippetViewSet):
    model = Resource
    icon = 'doc-full'
    menu_label = 'Resources'
    menu_order = 100
    list_display = ['name', 'category', 'author', 'status', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['status', 'author', 'category']

    content_panels = [
        FieldPanel('name'),
        FieldPanel('description'),
        FieldPanel('why_interesting'),
        FieldPanel('how_to'),
        FieldPanel('location'),
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


class PathwaySnippetViewSet(SnippetViewSet):
    model = Pathway
    icon = 'list-ul'
    menu_label = 'Pathways'
    menu_order = 200
    list_display = ['title', 'order', 'is_active']
    search_fields = ['title']

    panels = [
        FieldPanel('title'),
        FieldPanel('description'),
        FieldPanel('icon'),
        FieldPanel('order'),
        FieldPanel('is_active'),
    ]


register_snippet(ResourceSnippetViewSet)
register_snippet(ContributorSnippetViewSet)
register_snippet(PathwaySnippetViewSet)


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

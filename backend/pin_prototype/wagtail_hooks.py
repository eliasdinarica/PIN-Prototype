from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.admin.panels import FieldPanel, TabbedInterface, ObjectList
from .models import Resource, Pathway


class ResourceSnippetViewSet(SnippetViewSet):
    model = Resource
    icon = 'doc-full'
    menu_label = 'Resources'
    menu_order = 100
    list_display = ['name', 'category', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['category']

    content_panels = [
        FieldPanel('name'),
        FieldPanel('description'),
        FieldPanel('body'),
    ]

    meta_panels = [
        FieldPanel('category'),
        FieldPanel('subcategory'),
        FieldPanel('audiences'),
        FieldPanel('tags'),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading='Content'),
        ObjectList(meta_panels, heading='Settings'),
    ])



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
register_snippet(PathwaySnippetViewSet)

from django.db import migrations


def flat_to_sectioned(apps, schema_editor):
    """Wrap each Resource.body { blocks: [...] } into { sections: [{ title, body: { blocks: [...] } }] }."""
    Resource = apps.get_model('pin_prototype', 'Resource')
    for r in Resource.objects.all():
        body = r.body or {}
        if 'sections' in body:
            continue  # already in new format
        blocks = body.get('blocks', [])
        r.body = {
            'sections': [
                {'title': 'Contenu', 'body': {'blocks': blocks}},
            ] if blocks else []
        }
        r.save(update_fields=['body'])


def sectioned_to_flat(apps, schema_editor):
    Resource = apps.get_model('pin_prototype', 'Resource')
    for r in Resource.objects.all():
        body = r.body or {}
        if 'sections' not in body:
            continue
        all_blocks = []
        for sec in body.get('sections', []):
            inner = sec.get('body', {}).get('blocks', [])
            all_blocks.extend(inner)
        r.body = {'blocks': all_blocks}
        r.save(update_fields=['body'])


class Migration(migrations.Migration):

    dependencies = [
        ('pin_prototype', '0020_add_body_field'),
    ]

    operations = [
        migrations.RunPython(flat_to_sectioned, sectioned_to_flat),
    ]

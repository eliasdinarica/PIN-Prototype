from django.db import migrations


def populate_body(apps, schema_editor):
    """Backfill the new `body` StreamField from the legacy why/how/location
    fields so existing resources render identically through the new mechanism."""
    Resource = apps.get_model('pin_prototype', 'Resource')
    for res in Resource.objects.all():
        if res.body:  # already has sections — don't overwrite
            continue
        blocks_list = []
        for kind, html in (('why', res.why_interesting), ('how', res.how_to), ('location', res.location)):
            if html and str(html).strip():
                blocks_list.append(('section', {'kind': kind, 'heading': '', 'content': str(html)}))
        if blocks_list:
            res.body = blocks_list
            res.save(update_fields=['body'])


def noop(apps, schema_editor):
    # Reverse: the legacy fields are still populated, so nothing to undo.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pin_prototype', '0045_resource_body_resourcetranslation_body_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_body, noop),
    ]

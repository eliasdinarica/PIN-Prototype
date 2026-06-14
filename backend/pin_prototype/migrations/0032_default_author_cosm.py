from django.db import migrations


def create_default_author(apps, schema_editor):
    Contributor = apps.get_model('pin_prototype', 'Contributor')
    Resource = apps.get_model('pin_prototype', 'Resource')
    cosm, _ = Contributor.objects.get_or_create(name='COSM', defaults={'is_default': True})
    if not cosm.is_default:
        cosm.is_default = True
        cosm.save()
    Resource.objects.filter(author__isnull=True).update(author=cosm)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('pin_prototype', '0031_resource_status_contributor_resource_author'),
    ]

    operations = [
        migrations.RunPython(create_default_author, noop),
    ]

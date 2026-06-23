from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pin_prototype', '0036_pathway_category'),
    ]

    operations = [
        migrations.RenameModel(old_name='Pathway', new_name='Guide'),
        migrations.RenameModel(old_name='PathwayStep', new_name='GuideStep'),
        migrations.RenameField(model_name='guidestep', old_name='pathway', new_name='guide'),
    ]

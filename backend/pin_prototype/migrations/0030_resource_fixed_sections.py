import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pin_prototype', '0029_alter_profile_has_children'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resource',
            name='body',
        ),
        migrations.AddField(
            model_name='resource',
            name='why_interesting',
            field=wagtail.fields.RichTextField(blank=True, verbose_name='Why is it interesting?'),
        ),
        migrations.AddField(
            model_name='resource',
            name='how_to',
            field=wagtail.fields.RichTextField(blank=True, verbose_name='How to do it?'),
        ),
        migrations.AddField(
            model_name='resource',
            name='location',
            field=wagtail.fields.RichTextField(blank=True, verbose_name='Location'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='description',
            field=models.TextField(blank=True, help_text='Short intro shown at the top.'),
        ),
    ]

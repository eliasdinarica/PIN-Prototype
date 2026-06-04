from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pin_prototype', '0027_remove_category_priority'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='priority',
            field=models.IntegerField(default=0, help_text='Higher = shown first.'),
        ),
    ]

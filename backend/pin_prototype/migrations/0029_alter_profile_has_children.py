from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pin_prototype', '0028_add_category_priority'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='has_children',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]

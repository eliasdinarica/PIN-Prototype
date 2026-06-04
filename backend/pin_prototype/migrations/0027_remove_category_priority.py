from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pin_prototype', '0026_clear_old_body_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='priority',
        ),
    ]

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pin_prototype', '0025_alter_resource_body'),
    ]

    operations = [
        migrations.RunSQL(
            "UPDATE pin_prototype_resource SET body = '[]'",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]

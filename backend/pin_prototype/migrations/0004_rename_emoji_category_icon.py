from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pin_prototype', '0003_category_resource'),
    ]

    operations = [
        migrations.RenameField(
            model_name='category',
            old_name='emoji',
            new_name='icon',
        ),
        migrations.AlterField(
            model_name='category',
            name='icon',
            field=models.CharField(
                blank=True,
                max_length=50,
                choices=[
                    ('CurrencyDollarIcon', 'Money & Budget'),
                    ('BriefcaseIcon', 'Work'),
                    ('AcademicCapIcon', 'Education'),
                    ('HomeIcon', 'Housing'),
                    ('HeartIcon', 'Health'),
                    ('UsersIcon', 'Family'),
                    ('TruckIcon', 'Mobility'),
                    ('ScaleIcon', 'Rights & Duties'),
                    ('HandRaisedIcon', 'Help'),
                    ('GlobeAltIcon', 'Global / International'),
                    ('DocumentTextIcon', 'Documents'),
                    ('BuildingOfficeIcon', 'Administration'),
                    ('PhoneIcon', 'Contact'),
                    ('MapPinIcon', 'Location'),
                    ('ComputerDesktopIcon', 'Technology'),
                    ('ShieldCheckIcon', 'Security'),
                    ('ChatBubbleLeftIcon', 'Communication'),
                    ('StarIcon', 'Other'),
                ],
            ),
        ),
    ]

import recruitment.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='cv',
            field=models.FileField(blank=True, upload_to='cvs/%Y/%m/', validators=[recruitment.validators.validate_cv], verbose_name='CV'),
        ),
    ]

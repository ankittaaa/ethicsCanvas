# Generated by Django 2.0.3 on 2018-05-15 07:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0008_auto_20180515_0825'),
    ]

    operations = [
        migrations.AlterField(
            model_name='idea',
            name='text',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='idea',
            name='title',
            field=models.CharField(max_length=50),
        ),
    ]

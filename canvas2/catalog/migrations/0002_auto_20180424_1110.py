# Generated by Django 2.0.3 on 2018-04-24 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='idea',
            name='category',
            field=models.CharField(default='uncategorised', max_length=50),
        ),
        migrations.DeleteModel(
            name='IdeaCategory',
        ),
    ]

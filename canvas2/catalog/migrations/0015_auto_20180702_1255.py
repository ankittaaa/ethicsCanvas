# Generated by Django 2.0.5 on 2018-07-02 11:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0014_canvastag_idea'),
    ]

    operations = [
        migrations.AlterField(
            model_name='canvastag',
            name='idea',
            field=models.ManyToManyField(blank=True, db_index=True, related_name='tag_set', to='catalog.Idea'),
        ),
    ]

# Generated by Django 2.0.5 on 2018-07-05 15:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0019_auto_20180702_1435'),
    ]

    operations = [
        migrations.AlterField(
            model_name='canvas',
            name='project',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='canvas_set', to='catalog.Project'),
        ),
    ]

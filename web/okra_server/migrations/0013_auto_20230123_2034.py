# Generated by Django 3.1.7 on 2023-01-23 20:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('okra_server', '0012_auto_20230120_1651'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='experiment',
            options={'ordering': ['title', 'id']},
        ),
        migrations.AlterField(
            model_name='experiment',
            name='required_experiments',
            field=models.ManyToManyField(related_name='requiring_experiments', to='okra_server.Experiment'),
        ),
    ]

# Generated by Django 3.1.7 on 2023-01-20 14:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('okra_server', '0010_auto_20230119_2107'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='active',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='experiment',
            name='required_experiments',
            field=models.ManyToManyField(related_name='_experiment_required_experiments_+', to='okra_server.Experiment'),
        ),
    ]
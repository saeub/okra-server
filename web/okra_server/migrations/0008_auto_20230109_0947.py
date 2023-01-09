# Generated by Django 3.1.7 on 2023-01-09 09:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('okra_server', '0007_taskassignment_canceled'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='task',
            name='instructions_after',
        ),
        migrations.AddField(
            model_name='experiment',
            name='instructions_after_final_task',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='experiment',
            name='instructions_after_practice_task',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='experiment',
            name='instructions_after_task',
            field=models.TextField(null=True),
        ),
    ]

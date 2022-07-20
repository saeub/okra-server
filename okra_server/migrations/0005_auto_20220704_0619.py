# Generated by Django 3.1.7 on 2022-07-04 06:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('okra_server', '0004_auto_20210403_1039'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='task_type',
            field=models.CharField(choices=[('cloze', 'Cloze test'), ('digit-span', 'Digit span'), ('lexical-decision', 'Lexical decision'), ('n-back', 'n-back'), ('picture-naming', 'Picture-naming'), ('question-answering', 'Question answering'), ('reaction-time', 'Reaction time'), ('reading', 'Reading'), ('simon-game', 'Simon game'), ('trail-making', 'Trail making')], max_length=50),
        ),
        migrations.AlterField(
            model_name='task',
            name='data',
            field=models.JSONField(null=True),
        ),
    ]

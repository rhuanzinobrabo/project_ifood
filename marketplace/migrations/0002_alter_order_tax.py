# Generated by Django 5.1.7 on 2025-05-31 15:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='tax',
            field=models.TextField(blank=True, help_text='Dados das taxas aplicadas no formato JSON'),
        ),
    ]

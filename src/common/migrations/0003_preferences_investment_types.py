# Generated by Django 4.1 on 2022-09-27 21:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_preferences_email_api_key_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='preferences',
            name='investment_types',
            field=models.CharField(blank=True, max_length=20000, null=True),
        ),
    ]
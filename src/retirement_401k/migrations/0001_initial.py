# Generated by Django 2.2.28 on 2022-07-21 15:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account401K',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company', models.CharField(max_length=100)),
                ('start_date', models.DateField()),
                ('user', models.IntegerField()),
                ('goal', models.IntegerField(null=True)),
                ('notes', models.CharField(blank=True, max_length=40, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('employee_contribution', models.DecimalField(decimal_places=2, default=0, max_digits=20, null=True)),
                ('employer_contribution', models.DecimalField(decimal_places=2, default=0, max_digits=20, null=True)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=20, null=True)),
                ('roi', models.DecimalField(decimal_places=2, default=0, max_digits=20, null=True)),
                ('units', models.DecimalField(decimal_places=6, default=0, max_digits=20, null=True)),
                ('nav', models.DecimalField(decimal_places=6, default=0, max_digits=20, null=True)),
                ('nav_date', models.DateField(blank=True, null=True)),
                ('latest_value', models.DecimalField(decimal_places=2, default=0, max_digits=20, null=True)),
                ('gain', models.DecimalField(decimal_places=2, default=0, max_digits=20, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction401K',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trans_date', models.DateField()),
                ('notes', models.CharField(max_length=40)),
                ('employee_contribution', models.DecimalField(decimal_places=2, max_digits=20)),
                ('employer_contribution', models.DecimalField(decimal_places=2, max_digits=20)),
                ('units', models.DecimalField(decimal_places=6, max_digits=20)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='retirement_401k.Account401K')),
            ],
            options={
                'unique_together': {('account', 'trans_date')},
            },
        ),
        migrations.CreateModel(
            name='NAVHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nav_value', models.DecimalField(decimal_places=6, max_digits=20)),
                ('nav_date', models.DateField()),
                ('comparision_nav_value', models.DecimalField(decimal_places=6, default=0, max_digits=20)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='retirement_401k.Account401K')),
            ],
            options={
                'unique_together': {('account', 'nav_date')},
            },
        ),
    ]

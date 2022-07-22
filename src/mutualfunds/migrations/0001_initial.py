# Generated by Django 2.2.28 on 2022-07-21 15:05

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Folio',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('country', models.CharField(default='India', max_length=50)),
                ('folio', models.CharField(max_length=50)),
                ('user', models.IntegerField()),
                ('goal', models.IntegerField(blank=True, null=True)),
                ('units', models.DecimalField(blank=True, decimal_places=4, max_digits=20, null=True)),
                ('conversion_rate', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name='Conversion Price')),
                ('buy_price', models.DecimalField(blank=True, decimal_places=4, max_digits=20, null=True, verbose_name='Buy Price')),
                ('buy_value', models.DecimalField(blank=True, decimal_places=4, max_digits=20, null=True, verbose_name='Buy Value')),
                ('latest_price', models.DecimalField(blank=True, decimal_places=4, max_digits=20, null=True, verbose_name='Price')),
                ('latest_value', models.DecimalField(blank=True, decimal_places=4, max_digits=20, null=True, verbose_name='Value')),
                ('as_on_date', models.DateField(blank=True, null=True, verbose_name='As On Date')),
                ('gain', models.DecimalField(blank=True, decimal_places=4, max_digits=20, null=True, verbose_name='Gain')),
                ('notes', models.CharField(blank=True, max_length=80, null=True)),
                ('xirr', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name='XIRR')),
                ('fund', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='common.MutualFund')),
            ],
        ),
        migrations.CreateModel(
            name='Sip',
            fields=[
                ('folio', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='mutualfunds.Folio')),
                ('sip_date', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(31)], verbose_name='SIP Date')),
                ('amount', models.DecimalField(decimal_places=4, max_digits=20)),
            ],
        ),
        migrations.CreateModel(
            name='MutualFundTransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trans_date', models.DateField(verbose_name='Transaction Date')),
                ('trans_type', models.CharField(choices=[('Buy', 'Buy'), ('Sell', 'Sell')], max_length=10)),
                ('price', models.DecimalField(blank=True, decimal_places=4, max_digits=20, null=True, verbose_name='Price')),
                ('units', models.DecimalField(blank=True, decimal_places=4, max_digits=20, null=True)),
                ('conversion_rate', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name='Conversion Rate')),
                ('trans_price', models.DecimalField(blank=True, decimal_places=4, max_digits=20, null=True, verbose_name='Total Price')),
                ('broker', models.CharField(blank=True, max_length=20, null=True)),
                ('notes', models.CharField(blank=True, max_length=80, null=True)),
                ('switch_trans', models.BooleanField(default=False, verbose_name='Is a switch transaction?')),
                ('folio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mutualfunds.Folio')),
            ],
            options={
                'unique_together': {('folio', 'trans_date', 'trans_type', 'units', 'broker')},
            },
        ),
    ]

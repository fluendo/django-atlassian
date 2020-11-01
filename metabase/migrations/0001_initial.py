# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2020-10-31 16:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('django_atlassian', '0002_securitycontext_product_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='MetabaseConfiguration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site_url', models.CharField(max_length=256)),
                ('secret_key', models.CharField(max_length=256)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='django_atlassian.SecurityContext')),
            ],
        ),
    ]

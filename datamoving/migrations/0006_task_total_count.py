# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2019-06-25 10:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datamoving', '0005_delete_datasource'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='total_count',
            field=models.CharField(blank=True, max_length=2000, null=True, verbose_name='实际迁移量'),
        ),
    ]

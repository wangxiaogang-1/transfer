# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-06-03 16:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datamoving', '0003_auto_20190531_1048'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='rollback_condition',
            field=models.CharField(blank=True, max_length=2000, null=True, verbose_name='回灌条件'),
        ),
    ]

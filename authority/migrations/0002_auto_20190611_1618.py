# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-06-11 16:18
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authority', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='function',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='function',
            name='module',
        ),
        migrations.RemoveField(
            model_name='module',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='Function',
        ),
        migrations.DeleteModel(
            name='Module',
        ),
    ]
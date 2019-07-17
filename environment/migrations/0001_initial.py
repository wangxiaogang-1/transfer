# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-05-23 16:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='App',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('typer', models.SmallIntegerField(choices=[(0, 'DATASOURCE')], default=0, verbose_name='应用类型')),
                ('info', models.TextField(verbose_name='应用设置模板')),
                ('extend1', models.CharField(blank=True, max_length=255, null=True, verbose_name='备用字段1')),
                ('extend2', models.CharField(blank=True, max_length=255, null=True, verbose_name='备用字段2')),
                ('extend3', models.CharField(blank=True, max_length=255, null=True, verbose_name='备用字段3')),
            ],
            options={
                'db_table': 'app',
            },
        ),
        migrations.CreateModel(
            name='DataSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60, verbose_name='系统名称')),
            ],
        ),
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60, verbose_name='机器名称')),
                ('host', models.GenericIPAddressField(verbose_name='机器IP地址')),
                ('username', models.CharField(max_length=60, verbose_name='机器帐号')),
                ('password', models.CharField(max_length=255, verbose_name='机器密码')),
                ('protocol', models.SmallIntegerField(choices=[(0, 'SSH'), (1, 'TELNET')], default=0, verbose_name='连接协议')),
                ('port', models.IntegerField(default=22, verbose_name='连接端口')),
                ('extend1', models.CharField(blank=True, max_length=255, null=True, verbose_name='备用字段1')),
                ('extend2', models.CharField(blank=True, max_length=255, null=True, verbose_name='备用字段2')),
                ('extend3', models.CharField(blank=True, max_length=255, null=True, verbose_name='备用字段3')),
                ('apps', models.ManyToManyField(to='environment.App', verbose_name='应用列表')),
            ],
            options={
                'db_table': 'host',
            },
        ),
        migrations.AddField(
            model_name='app',
            name='belong_sys',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='environment.DataSet', verbose_name='归属系统'),
        ),
    ]

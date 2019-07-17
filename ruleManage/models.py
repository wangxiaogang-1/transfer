from django.contrib.auth.models import Group
from django.db import models


class Right(models.Model):
    name = models.CharField(verbose_name='权限名称', max_length=64)
    describe = models.TextField(verbose_name='权限描述')
    key = models.CharField(verbose_name='key', max_length=64)
    group_set = models.ManyToManyField(Group, verbose_name='用户组')

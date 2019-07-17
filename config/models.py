
from django.db import models


class Config(models.Model):
    key = models.CharField(max_length=500, verbose_name='键', default='', null=True, blank=True)
    value = models.CharField(max_length=500, verbose_name='值', default='', null=True, blank=True)
    info = models.CharField(max_length=500, verbose_name='配置名称', default='', null=True, blank=True)
    config_type = models.CharField(max_length=50, verbose_name='配置类型', default='', null=True, blank=True)
    class Meta:
        db_table = 'config'

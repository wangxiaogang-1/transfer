from django.db import models

# Create your models here.


class DataSet(models.Model):

    name = models.CharField(verbose_name='系统名称', max_length=60)


class App(models.Model):
    mod = (
        # (0, 'WEBLOGIC'),
        # (1, 'TOMCAT'),
        # (2, 'WARS'),
        # (3, 'MYSQL'),
        # (4, 'DB2'),
        (0, 'ORACLE'),
    )
    typer = models.SmallIntegerField(verbose_name='应用类型', choices=mod, default=0)
    info = models.TextField(verbose_name='应用设置模板')
    belong_sys = models.ForeignKey(DataSet, verbose_name='归属系统', null=True, on_delete=models.CASCADE)
    extend1 = models.CharField(verbose_name='备用字段1', max_length=255, null=True, blank=True)
    extend2 = models.CharField(verbose_name='备用字段2', max_length=255, null=True, blank=True)
    extend3 = models.CharField(verbose_name='备用字段3', max_length=255, null=True, blank=True)

    class Meta:
        # 定义model在数据库中的表名称
        db_table = "app"


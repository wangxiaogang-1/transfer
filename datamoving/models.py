from django.db import models


class Regulation(models.Model):
    rule_name = models.CharField(verbose_name='规则名称', max_length=30, unique=True)
    describe = models.CharField(verbose_name='规则描述', max_length=100, null=True, blank=True)
    belong_sys = models.SmallIntegerField(verbose_name='归属系统', null=True, blank=True)
    create_time = models.DateTimeField(verbose_name='规则创建时间', auto_now_add=True)
    create_user = models.CharField(verbose_name='创建人', max_length=10)
    table_info = models.TextField(verbose_name='表信息')
    # 文件名+时间戳
    rule_template = models.CharField(verbose_name='规则模板(存储过程?)', max_length=100)
    # 1 代表默认使用
    mod = (
        ("1", "启用临时表"),
        ("0", "不使用临时表"),
    )
    use_csr = models.SmallIntegerField(verbose_name='是否使用临时表', default='1', choices=mod)
    extend1 = models.CharField(verbose_name='备用字段1', max_length=255, null=True, blank=True)
    extend2 = models.CharField(verbose_name='备用字段2', max_length=255, null=True, blank=True)
    extend3 = models.CharField(verbose_name='备用字段3', max_length=255, null=True, blank=True)

    class Meta:
        # 定义model在数据库中的表名称
        db_table = "regulation"


class Task(models.Model):
    task_name = models.CharField(verbose_name='任务名称', max_length=30, unique=True)
    describe = models.CharField(verbose_name='任务描述', max_length=100, null=True, blank=True)
    RUN_WAY = (
        (0, "手动"),
        (1, "定时"),
    )
    run_way = models.SmallIntegerField(verbose_name='执行方式', choices=RUN_WAY)
    # auto_now =True 创建时或修改时都修改
    # auto_now_add =True 只在创建时进行赋值

    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    start_time = models.DateTimeField(verbose_name='开始时间', null=True, blank=True)
    end_time = models.DateTimeField(verbose_name='结束时间', null=True, blank=True)
    total_time = models.IntegerField(verbose_name='耗时', null=True, blank=True)
    STATUS = (
        (0, '未开始'),
        (1, '执行中'),
        (2, '执行失败'),
        (3, '执行成功'),
    )
    status = models.SmallIntegerField(verbose_name='任务状态', choices=STATUS)
    rule = models.ForeignKey(Regulation, verbose_name='规则id', null=True, on_delete=models.SET_NULL)
    # cron ?
    # start interval end ?

    time_rule = models.CharField(verbose_name='定时规则', max_length=255, null=True, blank=True)

    estimate_count = models.CharField(verbose_name='预估量', max_length=2000, null=True, blank=True)
    actual_count = models.CharField(verbose_name='实际量', max_length=2000, null=True, blank=True)
    commit_count = models.CharField(verbose_name='提交条数', max_length=20)
    total_count = models.CharField(verbose_name='实际迁移量', max_length=2000, null=True, blank=True)
    source_id = models.PositiveSmallIntegerField(verbose_name='数据源id', null=True, blank=True)
    target_id = models.PositiveSmallIntegerField(verbose_name='目标源id', null=True, blank=True)
    rollback_condition = models.CharField(verbose_name='回灌条件', max_length=2000, null=True, blank=True)
    TASK_TYPE = (
        (0, '迁移'),
        (1, '回灌'),
    )
    task_type = models.SmallIntegerField(verbose_name='任务类型', choices=TASK_TYPE)
    final_time = models.DateTimeField(verbose_name='定时结束时间', null=True, blank=True)
    step = models.IntegerField(verbose_name='执行阶段', null=True, blank=True)
    run_step = models.IntegerField(verbose_name='执行记录', null=True, blank=True)
    delete_count = models.CharField(verbose_name='删除量', max_length=2000, null=True, blank=True)
    sum_commit = models.IntegerField(verbose_name='总提交量', default=0)
    sum_delete = models.IntegerField(verbose_name='总删除量', default=0)
    database_status = models.CharField(verbose_name='数据源状态', max_length=50, default='')
    extend1 = models.CharField(verbose_name='备用字段3', max_length=255, null=True, blank=True)
    extend2 = models.CharField(verbose_name='备用字段3', max_length=255, null=True, blank=True)
    extend3 = models.CharField(verbose_name='备用字段3', max_length=255, null=True, blank=True)

    class Meta:
        # 定义model在数据库中的表名称
        db_table = "task"


class Log(models.Model):
    content = models.TextField(verbose_name='日志内容')
    task = models.ForeignKey(to=Task, verbose_name='任务外键', on_delete=models.CASCADE)

    class Meta:
        # 定义model在数据库中的表名称
        db_table = "log"

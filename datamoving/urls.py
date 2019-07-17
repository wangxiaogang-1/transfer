from django.conf.urls import url
from datamoving.views import *

urlpatterns = [
    url(r'^list/', task_list, name='task_list'),  # 作业列表
    url(r'^detail/', task_detail, name='task_detail'),  # 作业详细信息
    url(r'^add/', task_add, name='task_add'),  # 作业创建初始化
    url(r'^save/', task_save, name='task_save'),  # 作业创建初始化
    url(r'^delete/', task_delete, name='task_delete'),  # 删除作业
    url(r'^log/', task_log, name='task_log'),  # 作业日志
    url(r'^run/', task_run, name='task_run'),  # 作业批量执行(未完成)
    url(r'^init/', task_index_num, name='task_index_num'),  # 总览页数量部分
    url(r'^task/', task_list, name='task_index_task'),  # 总览页列表部分
    url(r'^bar_chart/', task_index_chart, name='task_index_chart'),  # 总览页图表部分
    url(r'^get_next_time/', get_next_time, name='get_next_time'),  # 获取下次定时时间
    url(r'^update_before/', update_before, name='update_before'),  # 更新初始化
    url(r'^update/', task_update, name='update'),  # 任务更新
    url(r'^get_next_count/', get_next_count, name='get_next_count'),  # 获取定时任务下一次更新数量
    url(r'^get_all_timing/', get_all_timing, name='get_all_timing'),  # 获取所有定时任务
    url(r'^hello_world/', hello_world, name='hello_world'),  # 测试hello world

]

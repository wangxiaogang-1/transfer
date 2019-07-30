from django.conf.urls import url
from ruleManage.views import *

urlpatterns = [
    url(r'^list/', rule_list, name='regular_list'), #规则列表
    url(r'^detail/', rule_detail, name='regular_detail'),#规则详情
    url(r'^update/', rule_update, name='regu;ar_update'),#规则更新
    url(r'^delete/', rule_delete, name='regular_delete'),#规则删除
    url(r'^save/', rule_add, name='rule_add'),#规则添加

    url(r'^right/list/', right_list, name='right_list'),  # 获取权限列表
    url(r'^right/change/', right_change, name='right_change'),  # 修改权限
]

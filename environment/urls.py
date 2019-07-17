from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^list/', data_list, name='data_list'),  # 数据源列表
    url(r'^detail/', data_detail, name='data_detail'),  # 数据源详细信息
    url(r'^save/', data_add, name='data_add'),  # 添加数据源
    url(r'^update/', data_update, name='data_change'),  # 修改数据源
    url(r'^delete/', data_delete, name='data_delete'),  # 删除数据源
    url(r'^test/', data_test, name='data_test'),  # 测试数据源
    url(r'^index/', index_main),  #总览页面的数据
    url(r'^init/', datasource_init, name='init'),  # 总览页面的数据


]


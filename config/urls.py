from django.conf.urls import url
from config.views import *

urlpatterns = [

    url(r'list/', config_list, name='config_list'),
    url(r'detail/', config_detail, name='config_detail'),  # 作业详细信息
    url(r'add/', config_add, name='config_add'),  # 作业详细信息

]

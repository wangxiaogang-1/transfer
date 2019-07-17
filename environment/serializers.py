import json

from rest_framework import serializers, pagination

# from environment.service import pass_decode
from environment.passwd_tool import AESCrypto
from .models import *


class ListPage(pagination.LimitOffsetPagination):
    """分页设置"""
    default_limit = 50  # 默认一页的数量
    max_limit = 100  # 一页最大的数量
    limit_query_param = 'limit'
    offset_query_param = 'offset'

class ListPage2(pagination.PageNumberPagination):
    """分页设置"""
    page_size = 50  # 默认一页的数量
    max_page_size = 100  # 一页最大的数量
    page_size_query_param = "size"
    page_query_param = "page"

def pass_decode_info(info):
    """传入数据源配置信息,根据password字段进行解密。格式修改成dict 一层关系"""
    data_dict = json.loads(info)
    for key, value in data_dict.items():
        if 'password' in key:
            value[0] = str(AESCrypto.decrypt(AESCrypto.doing(value[0])))
        data_dict[key] = value
    new_dict = {}
    for key, value in data_dict.items():
        new_dict[key] = value[0]
    return new_dict


class DataSourceSer(serializers.ModelSerializer):
    """数据源"""
    key = serializers.SerializerMethodField()
    info = serializers.SerializerMethodField()
    belong_sys = serializers.SerializerMethodField()

    def __init__(self, *args, m_flag=False, **kwargs):
        # m_flag = 是否返回详细信息
        super().__init__(*args, **kwargs)
        self.m_flag = m_flag

    class Meta:
        model = App
        fs = ('info', 'belong_sys', 'typer')
        fields = ('key', *fs)

    @staticmethod
    def get_key(obj):
        return obj.id

    def get_info(self, obj):
        dic = pass_decode_info(obj.info)
        if not self.m_flag:
            return {
                'datasource_name': dic.get('datasource_name'),  # 数据源名称
                'ip': dic.get('ip'),  # ip
            }
        return dic

    @staticmethod
    def get_belong_sys(obj):
        return obj.belong_sys_id, obj.belong_sys.name

from rest_framework import serializers, pagination
from config.models import Config


class ListPage2(pagination.PageNumberPagination):
    """分页设置"""
    page_size = 10  # 默认一页的数量
    max_page_size = 100  # 一页最大的数量
    page_size_query_param = "size"
    page_query_param = "page"


class ConfigListSer(serializers.ModelSerializer):
    """配置列表"""

    class Meta:
        model = Config
        fields = '__all__'


class ConfigDetailSer(serializers.ModelSerializer):
    """配置列表"""

    class Meta:
        model = Config
        fields = '__all__'

import json

from rest_framework import serializers, pagination
from environment.models import *
from datamoving.models import *


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


class RegulationListSerializer(serializers.ModelSerializer):
    belong_sys = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()

    class Meta:
        model = Regulation
        fields = ('id', 'rule_name', 'belong_sys', 'create_user', 'table_info', 'create_time')

    @staticmethod
    def get_id(obj):
        return obj.id

    @staticmethod
    def get_belong_sys(obj):
        return obj.belong_sys, DataSet.objects.get(id=obj.belong_sys).name


class RegulationDetailSerializer(serializers.ModelSerializer):
    belong_sys = serializers.SerializerMethodField()
    use_csr = serializers.SerializerMethodField()
    rule_template = serializers.SerializerMethodField()

    class Meta:
        model = Regulation
        fields = ('id', 'rule_name', 'describe', 'belong_sys', 'create_time', 'create_user',
                  'table_info', 'rule_template', 'use_csr')

    @staticmethod
    def get_belong_sys(obj):
        return obj.belong_sys, DataSet.objects.get(id=obj.belong_sys).name

    @staticmethod
    def get_rule_template(obj):
        return obj.rule_template[obj.rule_template.rfind('/') + 1:][14:]

    @staticmethod
    def get_use_csr(obj):
        chinese_mean = ''
        for mo in Regulation.mod:
            if str(obj.use_csr) == mo[0]:
                chinese_mean = mo[1]
        return obj.use_csr, chinese_mean
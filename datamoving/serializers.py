from rest_framework import serializers, pagination
from .models import *
import json
from datamoving.time_tool import cal_datetime


class ListPage(pagination.LimitOffsetPagination):
    """分页设置"""
    default_limit = 10  # 默认一页的数量
    max_limit = 100  # 一页最大的数量
    limit_query_param = 'limit'
    offset_query_param = 'offset'


class ListPage2(pagination.PageNumberPagination):
    """分页设置"""
    page_size = 10  # 默认一页的数量
    max_page_size = 100  # 一页最大的数量
    page_size_query_param = "size"
    page_query_param = "page"


class TaskListSer(serializers.ModelSerializer):
    """作业列表"""
    key = serializers.SerializerMethodField()
    run_way = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    create_time = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    total_time = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fs = ('task_name', 'run_way', 'status', 'create_time', 'start_time', 'end_time',
              'total_time')
        # 'estimate_count', 'actual_count', 'delete_count'
        fields = ('key', *fs)


    @staticmethod
    def get_total_time(obj):
        if obj.start_time is None or obj.end_time is None:
            return ''
        else:
            return cal_datetime(obj.start_time, obj.end_time)
    @staticmethod
    def get_create_time(obj):
        return obj.create_time.strftime('%Y-%m-%d %H:%M:%S') if obj.create_time is not None else None

    @staticmethod
    def get_start_time(obj):
        return obj.start_time.strftime('%Y-%m-%d %H:%M:%S') if obj.start_time is not None else None

    @staticmethod
    def get_end_time(obj):
        return obj.end_time.strftime('%Y-%m-%d %H:%M:%S') if obj.end_time is not None else None

    @staticmethod
    def get_key(obj):
        return obj.id

    @staticmethod
    def get_run_way(obj):
        return obj.get_run_way_display()

    @staticmethod
    def get_status(obj):
        return obj.get_status_display()


class TaskDetailSer(serializers.ModelSerializer):
    """作业详细信息"""
    run_way = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    task_type = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = '__all__'

    @staticmethod
    def get_run_way(obj):
        return obj.run_way, obj.get_run_way_display()

    @staticmethod
    def get_status(obj):
        return obj.status, obj.get_status_display()

    @staticmethod
    def get_task_type(obj):
        return obj.task_type, obj.get_task_type_display()


class LogInit(serializers.ModelSerializer):
    total_count = serializers.SerializerMethodField()
    create_time = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    main_count = serializers.SerializerMethodField()
    e_count = serializers.SerializerMethodField()
    emain_count = serializers.SerializerMethodField()
    database_status = serializers.SerializerMethodField()
    class Meta:
        model = Task
        fs = ('task_name', 'create_time', 'status', 'run_way', 'start_time', 'end_time',)
        fields = (*fs, 'total_count', 'main_count', 'e_count', 'emain_count', 'database_status')

    @staticmethod
    def get_database_status(obj):

        return "{}" if obj.database_status == '' else obj.database_status

    @staticmethod
    def get_create_time(obj):
        return obj.create_time.strftime('%Y-%m-%d %H:%M:%S') if obj.create_time is not None else None

    @staticmethod
    def get_start_time(obj):
        return obj.start_time.strftime('%Y-%m-%d %H:%M:%S') if obj.start_time is not None else None

    @staticmethod
    def get_end_time(obj):
        return obj.end_time.strftime('%Y-%m-%d %H:%M:%S') if obj.end_time is not None else None


    @staticmethod
    def get_total_count(obj):
        total_count = 0 if not obj.actual_count else json.loads(obj.actual_count)

        if not total_count:
            return total_count
        return sum(total_count.values())

    @staticmethod
    def get_main_count(obj):
        total_count = 0 if not obj.actual_count else json.loads(obj.actual_count)
        if not total_count:
            return total_count
        return next(iter(total_count.values()))

    @staticmethod
    def get_e_count(obj):
        estimate_count = 0 if not obj.estimate_count else json.loads(obj.estimate_count)
        if not estimate_count:
            return estimate_count
        return sum(estimate_count.values())

    @staticmethod
    def get_emain_count(obj):
        estimate_count = 0 if not obj.estimate_count else json.loads(obj.estimate_count)
        if not estimate_count:
            return estimate_count
        return next(iter(estimate_count.values()))


if __name__ == '__main__':

    pass

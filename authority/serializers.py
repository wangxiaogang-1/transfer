from rest_framework import serializers, pagination
from django.contrib.auth.models import User, Group
from ruleManage.models import *
from ruleManage.right_tools import get_user_rights


class ListPage(pagination.LimitOffsetPagination):
    """分页设置"""
    default_limit = 100  # 默认一页的数量
    max_limit = 100  # 一页最大的数量
    limit_query_param = 'limit'
    offset_query_param = 'offset'


class ListPage2(pagination.PageNumberPagination):
    """分页设置"""
    page_size = 100  # 默认一页的数量
    max_page_size = 100  # 一页最大的数量
    page_size_query_param = "size"
    page_query_param = "page"


class UserListSerilizer(serializers.ModelSerializer):
    """用户list"""
    last_login = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'first_name', 'username', 'last_login')

    @staticmethod
    def get_last_login(obj):
        return obj.last_login.strftime('%Y-%m-%d %H:%M:%S') if obj.last_login else None


class UserDetailSer(serializers.ModelSerializer):
    """查看user详情"""

    class Meta:
        model = User
        fields = ('username', 'first_name', 'groups')


class GroupListSer(serializers.ModelSerializer):
    """用户组list"""
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ('id', 'name')

    @staticmethod
    def get_id(obj):
        return obj.id

    @staticmethod
    def get_name(obj):
        return obj.name


class GroupDetailSer(serializers.ModelSerializer):
    """用户组的detail"""
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    rights = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ('id', 'name', 'user', 'rights')

    @staticmethod
    def get_id(obj):
        return obj.id

    @staticmethod
    def get_name(obj):
        return obj.name

    @staticmethod
    def get_user(obj):
        group = Group.objects.get(id=obj.id)
        return [user['id'] for user in group.user_set.all().values('id')]

    @staticmethod
    def get_rights(obj):
        group = Group.objects.get(id=obj.id)

        return [right['id'] for right in group.right_set.all().values('id')]


class AuthDetailSer(serializers.Serializer):
    """作业详细信息"""

    user = serializers.SerializerMethodField()
    permission = serializers.SerializerMethodField()

    class Meta:
        fields = '__all__'

    @staticmethod
    def get_user():
        return User.objects.all().values('id', 'username', 'first_name')

    @staticmethod
    def get_permission():
        return Right.objects.all().values('id', 'name')


# class User_Right_Init(serializers):
#     class Meta:
#         pass


if __name__ == '__main__':

    pass

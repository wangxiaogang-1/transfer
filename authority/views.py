# coding:utf-8

import hashlib
import logging
import os, django, time
import json
from django.contrib.auth import authenticate, logout

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transfer.settings")
django.setup()
from rest_framework.response import Response
from rest_framework.decorators import api_view
from authority.serializers import *
from rest_framework import status
from ruleManage.models import *
from datamoving.public_params import EXIST, SUCCESS, ERROR
from ruleManage.right_tools import *
from datetime import datetime
logg = logging.getLogger('autoops')


@api_view(['POST'])
def login(request):
    """登陆   0用户名和密码输入正确 登陆成功"""
    if request.method == "GET":
        return Response(status.HTTP_400_BAD_REQUEST)
    elif request.method == "POST":
        dic = request.data
        logg.info(dic['username'])
        user = authenticate(username=dic['username'], password=dic['password'])
        if user:
            # 获取用户所对应的组有哪些权限
            result = get_user_rights(user)
            User.objects.filter(id=user.id).update(last_login=datetime.now())
            user_json = {'id': user.id, 'username': user.username, 'first_name': user.first_name,
                         'is_super': user.is_superuser}
            return Response({'result': SUCCESS, "right": result, 'user': user_json})
        else:
            return Response(ERROR)


@api_view(['GET'])
def log_out(request):
    """退出,  回到登陆页面0"""
    logg.info(request.user.username)
    try:
        logout(request)
    except Exception as e:
        print(e)
        return Response(ERROR)
    return Response(SUCCESS)


@api_view(['GET'])
# @right_required(['c'])
def regist_init(request):
    groups = Group.objects.all().values('id', 'name')
    return Response(groups)


@api_view(['POST'])
def registe(request):
    """注册"""
    _register = request.data
    if not _register:
        # 没有获取到数据
        return Response(ERROR)
    try:
        old_user = User.objects.filter(username=_register['user']['username'])
        if old_user:
            return Response(EXIST)
        user = User.objects.create(**_register['user'])
        user.set_password(_register['user']['password'])
        user.save()
        gids = _register['groups']
        for gid in gids:
            group = Group.objects.get(id=gid)
            group.user_set.add(user.id)
        if user:
            return Response(SUCCESS)
    except Exception as e:
        return Response(ERROR)


@api_view(['GET'])
def user_list(request):
    """用户list传入username,first_name用户查询"""
    print(request.user.username)
    dic = request.query_params
    print(dic, 'dic')
    list_data = []
    if dic:
        users = User.objects.filter(username__icontains=dic['username']).filter(
            first_name__icontains=dic['first_name']).values('id')
        xx = [user['id'] for user in users]
        groups = Group.objects.filter(user__in=xx).distinct()
        for group in groups:
            g = group.user_set.filter(id__in=xx).all()
            users = UserListSerilizer(instance=g, many=True)
            list_data.append({'id': group.id, 'name': group.name, 'users': users.data})
    else:
        groups = Group.objects.all()
        for group in groups:
            g = list(group.user_set.values('id', 'first_name'))
            list_data.append({'id': group.id, 'name': group.name, 'users': g})
    return Response(list_data)


@api_view(['GET'])
def user_list1(request):
    """"""
    _user = request.query_params
    print(_user, '_user')




@api_view(['GET'])
def user_delete(request):
    """删除用户  1 表示删除失败   0删除成功"""
    id = request.GET.get('id')
    if not id:
        return Response(status.HTTP_400_BAD_REQUEST)
    try:
        User.objects.filter(id=id).delete()
    except Exception as e:
        return Response(ERROR)
    return Response(SUCCESS)


@api_view(['GET'])
def user_detail(request):
    """用户信息展示get,detail/?id=1"""
    id = request.GET.get('id')
    if not id:
        return Response(ERROR)
    try:
        user_info = User.objects.get(id=id)
        user_ser = UserDetailSer(user_info)
    except Exception as e:
        return Response(ERROR)
    return Response(user_ser.data)


@api_view(['POST'])
def user_update(request):
    """
    用户信息修改
    :param request:
    :return:
    """
    data = dict(request.data)
    if not data:
        return Response(status.HTTP_400_BAD_REQUEST)
    try:
        User.objects.filter(id=data['user']['id']).update(**data['user'])
        user = User.objects.get(id=data['user']['id'])
        if data['groups']:
            groups = Group.objects.all()
            for group in groups:
                group.user_set.remove(user)
                group.save()
            for group in Group.objects.filter(id__in=data['groups']):
                group.user_set.add(user)
                group.save()
    except Exception as e:
        return Response(ERROR)
    return Response(SUCCESS)


@api_view(['POST'])
def user_password_check(request):
    # 参数：原密码，新密码(2次)
    """
    :param username:
    :return: old_password
             new_password
    """
    dic = request.data
    user = User.objects.get(id=dic['id'])
    result = user.check_password(dic['password'])

    if result:
        return Response(SUCCESS)
    else:
        return Response(ERROR)


@api_view(['POST'])
def user_password_update(request):
    # 参数：原密码，新密码(2次)
    """
    :param username:
    :return: password
    """
    dic = request.data
    user = User.objects.get(id=dic['id'])
    # user = authenticate(username=dic['username'], password=dic['old_password'])
    if user:
        result = user.set_password(dic['password'])
        user.save()
        return Response(SUCCESS)
    else:
        return Response(ERROR)


@api_view(['GET'])
def group_list(request):
    """用户组list"""
    dic = {}
    name = request.GET.get('name')
    if name:
        dic['name__contains'] = name
    group = Group.objects.filter(**dic).order_by('-id')
    page = ListPage2()
    page_roles = page.paginate_queryset(queryset=group, request=request)
    roles_ser = GroupListSer(instance=page_roles, many=True)
    size_count = group.count()
    size = int(request.GET.get('size') or ListPage2.page_size)
    return Response({
        'size_count': size_count,
        'page_count': int((size_count + size - 1) / size),  # 向上取整
        'results': roles_ser.data,
    })


@api_view(['GET'])
def group_detail(request):
    id = request.GET.get('id')
    if not id:
        return Response(status.HTTP_400_BAD_REQUEST)
    try:
        group_info = Group.objects.get(id=id)
        group_ser = GroupDetailSer(group_info)
    except Exception as e:
        print(e)
        return Response(status.HTTP_400_BAD_REQUEST)
    return Response(group_ser.data)


@api_view(['GET'])
def group_delete(request):
    """组删除  0删除成功   1删除失败"""
    gid = request.GET.get('id')
    if not gid:
        return Response(ERROR)
    result = Group.objects.filter(id=gid).delete()
    if result[1]:
        return Response(SUCCESS)
    else:
        return Response(ERROR)


@api_view(['GET'])
def group_add_init(request):
    right = AuthDetailSer.get_permission()
    user = AuthDetailSer.get_user()
    return Response({'user': user, 'right': right})


@api_view(['POST'])
def group_add(request):
    """
    创建组的同时,添加了组下的用户和权限
    :param request:
    :return:
    """
    data = request.data
    print(data)
    if not data:
        return Response(ERROR)
    name = data['name']
    count = Group.objects.filter(name=name).count()
    if count > 0:
        return Response(EXIST)
    try:
        group = Group.objects.create(name=name)
    except Exception as e:
        print(e)
        return Response(ERROR)
    group = Group.objects.get(id=group.id)
    group.user_set.clear()
    group.user_set.add(*data['users'])
    group.right_set.clear()
    group.right_set.add(*data['rights'])
    return Response(SUCCESS)


@api_view(['POST'])
def group_update(request):
    """
    更新组，以及组下的用户和权限
    :param request:
    :return:
    """
    data = request.data
    if not data:
        return Response(ERROR)
    try:
        Group.objects.filter(id=data['id']).update(name=data['name'])
    except Exception as e:
        print(e)
        return Response(ERROR)
    group = Group.objects.get(id=data['id'])
    group.user_set.clear()
    group.user_set.add(*data['users'])
    group.right_set.clear()
    group.right_set.add(*data['rights'])
    return Response(SUCCESS)


def md5_encrip(password):
    """md5密码加密"""
    enc = hashlib.md5()
    enc.update(str(password).encode(encoding='utf-8'))
    return enc.hexdigest()


if __name__ == '__main__':
    # from rest_framework import
    # print(request.)
    pass

import json
from django.core import serializers
from .models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, User, Permission
from django.db.models import Q
from django.shortcuts import HttpResponse
from tool.data_tool import *
import tool.constant as cfg

QUERYSET_FIRST_ELEM = cfg.SystemConfigs.QUERYSET_FIRST_ELEM

truth_table = {
    'status': {
        True: 1,
        False: 0
    }
}


# 获取用户组列表
def getUserGroupList():
    return HttpResponse(trans_data(serializers.serialize("json", Group.objects.all().order_by('id'))))


# 获取用户组列表
def ug_init():
    data = {
        'modules': json.loads(trans_data(serializers.serialize("json", Module.objects.all()))),
        'users': json.loads(trans_data(serializers.serialize("json", User.objects.all()))),
    }
    return HttpResponse(json.dumps(data))


# 初始化新增/更新用户数据
def initCreateOrUpdateUser(request):
    opt = request.GET.get('opt')
    init_data = {'groups': Group.objects.all().values().order_by('id')}
    user_iden = None
    init_data['user_iden'] = user_iden.confV.split(',')
    user_status = None
    init_data['user_status'] = user_status.confV.split(',')
    init_data['user_groups'] = []
    init_data['user'] = {}
    if opt == 'u':
        user = User.objects.get(id=request.GET.get('uid'))
        init_data['user_groups'] = user.groups.all().values().order_by('id')
        init_data['user'] = User.objects.filter(id=request.GET.get('uid')).values()[QUERYSET_FIRST_ELEM]
    return init_data


# 通过用户ID获得group的列表
def getUserGroupListByUserId(request):
    result_list = []
    groups = Group.objects.filter(user__id=request.POST.get('userId')).values_list('id').order_by('id')
    for i in groups:
        result_list.append(i)
    return result_list


def instance(obj, fields):
    """
    实例化一个Queryset, 并按照type返回数据，json str queryset, ** 实验性功能 **
    :param obj:
    :param fields:
    :return:
    """
    result = []
    for filed in fields:
        result.append(obj.object.get(**filed))
    return result


def init_group(request):
    """
    更新用户组时根据主键初始化用户组信息
    :param request:
    :return:
    """
    gid = request.POST.get('gid')
    group = Group.objects.get(id=gid)
    userset = list(group.user_set.all().values('id'))
    users = []
    for u in userset:
        users.append(u['id'])
    permissions = list(group.permissions.filter(content_type__model='module').values('id', 'codename'))
    modules = []
    for perm in permissions:
        modules.append(list(Module.objects.filter(codename=perm['codename']).values())[0]['id'])
    data = {
        "id": group.id,
        "name": group.name,
        "users": users,
        "modules": modules
    }
    return json.dumps(data)


def save_group(request):
    """
    保存用户组和关联的权限、用户
    :param request:
    :return:
    """
    result = ''
    if request.method == 'POST':
        group = json.loads(request.POST['group'])
        if len(Group.objects.filter(name=group['name'])) > 0 and request.POST['type'] == 'add':
            result = 'warning'
            return result
        group_id = group['id'] or -1
        saved, created = Group.objects.update_or_create(id=group_id, defaults={'name': group['name']})
        users = []
        permissions = []
        for uid in group['users']:
            users.append(User.objects.get(id=uid))
        for mid in group['modules']:
            mod = Module.objects.get(id=mid)
            permissions.append(Permission.objects.get(codename=mod.codename))
        saved.user_set.all().delete()
        saved.user_set.set(users)
        saved.permissions.all().delete()
        saved.permissions.set(permissions)
        result = 'success'
    else:
        result = 'error'
    return result


# 查询组信息
def getUserGroupsByKeyword(request):
    result_list = []
    userGroupList = {}
    if request.method == 'POST':
        keyword = request.POST['keyword']
        result = Group.objects.filter(name__contains=keyword).values_list('id', 'name')
        for i in result:
            result_list.append(i)
        result_list = queryset_transducer(result_list)
        new_dict = {}
        for i in result_list:
            new_dict[i[QUERYSET_FIRST_ELEM]] = i[1]
        userGroupList = json.dumps({"data": new_dict, "keyword": keyword})
    return HttpResponse(userGroupList)


# 更新组信息
def updateUserGroup(request):
    if request.method == 'POST':
        ugid = request.POST['id']
        name = request.POST['name']
        Group.objects.filter(id=ugid).update(name=name)
        result = 'success'
    else:
        result = 'failed'
    return HttpResponse(result)



def deleteUserGroup(request):
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        result = Group.objects.filter(id=int(group_id)).delete()
        print(result)
        result = 'success'
    else:
        result = 'failed'
    return HttpResponse(result)


# 初始化用户数据列表
def initUserList(request):
    result_list = []
    users = User.objects.all().values('id', 'username', 'first_name', 'last_name', 'is_superuser')
    for i in users:
        result_list.append(i)
    g_users = getUsersByUserGroupId(request)
    for ul in result_list:
        for gul in g_users:
            if ul['id'] == gul['id']:
                ul['statusClass'] = True
    userList = json.dumps({"users": result_list})
    return HttpResponse(userList)


# 组成员管理
def addUserToUserGroup(request):
    result = 'success'
    if request.method == 'POST':
        userGroupId = request.POST['userGroupId']
        userid_list = json.loads(request.POST.get('userIds'))
        group = Group.objects.get(id=userGroupId)
        group.user_set.clear()
        for userid in userid_list:
            group.user_set.add(User.objects.get(id=int(userid)))
    else:
        result = 'failed'
    return HttpResponse(result)


# 获得用户的列表
def getUsers():
    users = User.objects.all().values('id', 'username', 'first_name', 'last_name', 'last_login', 'date_joined',
                                      'is_superuser', 'is_active')

    return users


# 通过用户组ID获获取用户列表
def getUsersByUserGroupId(request):
    result_list = []
    ugid = request.POST.get('userGroupId')
    users = User.objects.filter(groups__id=ugid).values('id', 'first_name', 'last_name', 'username')
    for i in users:
        result_list.append(i)
    return result_list


# 通过用户组ID获获取用户列表
def getUserByIdForInitUpdate(request):
    result_list = []
    uid = int(request.POST.get('userId'))
    user = User.objects.filter(id=uid).values()
    groupsInUser = queryset_transducer(Group.objects.filter(user__id=uid).values_list('id'))
    for i in user:
        result_list.append(i)
    user = result_list[QUERYSET_FIRST_ELEM]
    del user['password'], user['date_joined'], user['last_login'], user['is_staff']
    user['is_active'] = truth_table['status'][user['is_active']]
    user['is_superuser'] = truth_table['status'][user['is_superuser']]
    user['groupsInUser'] = groupsInUser.__str__()
    return user.__str__()


# 修改用户密码
def changePassword(request):
    uid = request.POST.get('userId')
    newPasswd = request.POST.get('newPasswd')
    user = User.objects.get(id=uid)
    user.set_password(newPasswd)
    user.save()
    return 'success'


# 查询用户信息
def getUsersByKeyword(request):
    result_list = []
    userList = {}
    if request.method == 'POST':
        keyword = request.POST['keyword']
        result = User.objects.filter(name__contains=keyword).values_list('id', 'username')
        for i in result:
            result_list.append(i)
        result_list = queryset_transducer(result_list)
        new_dict = {}
        for i in result_list:
            new_dict[i[QUERYSET_FIRST_ELEM]] = i[1]
        userList = json.dumps({"data": new_dict, "keyword": keyword})
    return HttpResponse(userList)


# 初始化组数据列表
def initGroupList():
    result_list = []
    groups = Group.objects.all().values('id', 'name')
    for i in groups:
        result_list.append(i)
    data = {"userGroups": result_list}
    userList = json.dumps(data)
    return userList


def add_user(request):
    """
    初始化新建或更新用户时数据
    :param request:
    :return:
    """
    uid = request.POST.get('user_id')
    user_groups = []
    data = {
        'user': {},
        'groups': list(Group.objects.all().values()),
        'groups_selected': []
    }
    if uid != '':
        uobj = User.objects.get(id=uid)
        user_groups = uobj.groups.all()
        data['user'] = list(User.objects.filter(id=uid).values('id', 'username', 'last_name', 'email', 'is_superuser', 'is_active', 'is_staff'))
        for ug in user_groups:
            data['groups_selected'].append(ug.id)
    return json.dumps(data)


def save_user(request):
    """
    新建系统用户
    :param request:
    :return:
    """
    result = 'success'
    if request.method == 'POST':
        opt_type = request.POST.get('type')
        user = json.loads(request.POST.get('user'))
        if User.objects.filter(username=user['username']).__len__() == 0 and opt_type == 'add':
            result = 'warning'
            return result
        groups_selected = json.loads(request.POST.get('groups_selected'))
        print(user)
        saved, created = User.objects.update_or_create(username=user['username'], defaults=user)
        if opt_type == 'add':
            saved.set_password(user['password'])
        if len(groups_selected) != 0:
            saved.groups.clear()
            saved.groups.set(groups_selected)
        saved.save()
    else:
        result = 'error'
    return result


def remove_user(request):
    """
    删除系统用户
    :param request:
    :return:
    """
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        r = User.objects.filter(id=int(user_id)).delete()
        result = 'success'
    else:
        result = 'failed'
    return HttpResponse(result)


def set_user_pwd(request):
    """
    修改用户密码
    :param request:
    :return:
    """
    uid = request.POST.get('user_id')
    user = User.objects.get(id=uid)
    pwd = request.POST.get('password')
    user.set_password(pwd)
    user.save()
    return get_check_pwd(user, pwd)


def check_pwd(request):
    """
    检测用户密码是否正确
    :param request:
    :return:
    """
    uid = request.POST.get('user_id')
    user = User.objects.get(id=uid)
    pwd = request.POST.get('password')
    return get_check_pwd(user, pwd)


def get_check_pwd(user, pwd):
    """
    检测用户密码是否匹配
    :param user: 待检测的User对象
    :param pwd: 待检测的用户明文密码
    :return: result: 检测结果
    """
    if user.check_password(pwd):
        return 'success'
    return 'failed'


# 获取所有权限
def permissionList():
    result_list = []
    permissions = Permission.objects.all().values('id', 'name')
    for i in permissions:
        result_list.append(i)
    uig = getUsersInnerGroups()
    return {"permission": result_list, "uag": uig}


# 获取所有组和组中所有用户
def getUsersInnerGroups():
    result = {
        'userInGroup': [],
        'userNotInGroup': []
    }
    groups = Group.objects.all().values('id', 'name')
    all_user = User.objects.filter(groups=None).values('id', 'first_name', 'last_name', 'username')
    for user in all_user:
        result['userNotInGroup'].append(user)
    for group in groups:
        userInGroup = User.objects.filter(groups__id=group['id']).values('id', 'first_name', 'last_name', 'username')
        group['users'] = []
        for i in userInGroup:
            group['users'].append(i)
        grop = Group.objects.get(id=group['id'])
        if len(grop.user_set.all()) != 0:
            result['userInGroup'].append(group)
    return result


# 查找权限信息
def getPermissionByKeyword(request):
    result_list = []
    permList = {}
    if request.method == 'POST':
        keyword = request.POST['keyword']
        result = Permission.objects.filter(name__contains=keyword).values_list('id', 'name')
        for i in result:
            result_list.append(i)
        result_list = queryset_transducer(result_list)
        new_dict = {}
        for i in result_list:
            new_dict[i[QUERYSET_FIRST_ELEM]] = i[1]
        permList = json.dumps({"data": new_dict, "keyword": keyword})
    return HttpResponse(permList)


# 初始化所有权限a
def initPermission(request):
    result_list = [{'permissionId': dict(json.loads(initGroupList()), **json.loads(initUserList(request)))}]
    data = json.dumps({'data': result_list})
    return HttpResponse(data)


# 获取所有拥有该权限的组和用户
def getUsersAndUsersGroupsInPermission(request):
    result_list, result_list2, result_list3 = [], [], []
    data = {}
    if request.method == 'POST':
        permissionId = int(request.POST['permissionId'])
        groups = Group.objects.filter(Q(permissions__id=permissionId)).values_list('id').distinct()
        for group in groups:
            result_list.append(group[QUERYSET_FIRST_ELEM])
        users = User.objects.filter(Q(user_permissions=permissionId)).values_list('id').distinct()
        for user in users:
            result_list2.append(user[QUERYSET_FIRST_ELEM])
        data = {'permissionId': permissionId, 'usersGroup': result_list, 'users': result_list2}
    return data


# 更新请求的权限关联的所有用组和用户
def updateUsersAndUsersGroupsInPermission(request):
    if request.method == 'POST':
        data = json.loads(request.POST.get('data'))
        permissionId = int(data['permissionId'])
        permission = Permission.objects.get(id=permissionId)
        permission.user_set.clear()
        permission.group_set.clear()
        userGroups = data['userGroups']
        users = data['users']
        for gid in userGroups:
            ug = Group.objects.get(id=int(gid))
            permission.group_set.add(ug)
        for uid in users:
            user = User.objects.get(id=int(uid))
            permission.user_set.add(user)
        result = 'success'
    else:
        result = 'failed'
    return HttpResponse(result)


# 获取组拥有的全部权限
def getGroupPermission(request):
    groupId = int(request.POST.get('groupId'))
    group = Group.objects.get(id=groupId)
    permissions = group.permissions.all().values_list('id')
    result = []
    for p in permissions:
        result.append(p[QUERYSET_FIRST_ELEM])
    return result.__str__()


# 获取用户拥有的全部权限
def getUserPermission(request):
    userId = int(request.POST.get('userId'))
    User.objects.get(id=userId)
    permissions = Permission.objects.filter(user__id=userId).values_list('id')
    result = []
    for p in permissions:
        result.append(p[QUERYSET_FIRST_ELEM])
    return result.__str__()


# 为组批量添加权限
def savePermissionToGroup(request):
    data = json.loads(request.POST.get('data'))
    groupId = int(data['groupId'])
    group = Group.objects.get(id=groupId)
    permissionIds = data['permissions']
    group.permissions.clear()
    for pid in permissionIds:
        permission = Permission.objects.get(id=int(pid))
        group.permissions.add(permission)
    return 'success'


# 为用户批量添加权限
def savePermissionToUser(request):
    data = json.loads(request.POST.get('data'))
    userId = int(data['userId'])
    user = User.objects.get(id=userId)
    permissionIds = data['permissions']
    user.user_permissions.clear()
    for pid in permissionIds:
        permission = Permission.objects.get(id=int(pid))
        user.user_permissions.add(permission)
    return 'success'


# 为组和用户批量添加权限
def savePermissionToGroupOrUser(request):
    data = json.loads(request.POST.get('data'))
    groupId = int(data['groupId'])
    userId = int(data['userId'])
    result = 'failed'
    if groupId == -1:
        result = savePermissionToUser(request)
    elif userId == -1:
        result = savePermissionToGroup(request)
    return result


# 登录
def auth_login(request):
    result = {
        'status': '0000',
        'modules': [],
        'user': {}
    }
    username = request.POST.get('username')
    passwd = request.POST.get('password')
    user = authenticate(username=username, password=passwd)
    if user is not None:
        user_msg = {}
        user_p = \
            User.objects.filter(username=username).values('id', 'username', 'first_name', 'last_name', 'is_superuser',
                                                          'is_active', 'email')[QUERYSET_FIRST_ELEM]
        for key in user_p:
            user_msg[key] = user_p[key]
        modules = getUserModules(user_msg)
        if len(modules) == 0:
            result['status'] = '0002'
            return result
        login(request, user)
        result['modules'] = modules
        result['user'] = user_msg
    else:
        result['status'] = '0001'
    return result


# 获取用户有可用的模块权限
def getUserModules(login_user):
    user = User.objects.get(id=login_user['id'])
    groups = Group.objects.filter(user=user)
    modules = []
    for g in groups:
        permissions = list(Permission.objects.filter(group=g).order_by('id').values())
        for perm in permissions:
            modules.append(list(Module.objects.filter(codename=perm['codename']).values())[0])
    return modules


# 获取用户可用的功能权限
def getUserFunction(login_user):
    user = User.objects.get(id=login_user['id'])
    functions = []
    all_permission = Permission.objects.filter(content_type__model='function').values()
    for permission in all_permission:
        if user.has_perm('module.' + permission['codename']):
            q_function = Function.objects.filter(content_type__model='function',
                                                 codename=permission['codename']).values_list()
            for f_field in q_function:
                functions.append(f_field)
    return functions


def check_login(request):
    """
    检查用户授权
    :param request:
    :return:
    """
    return request.user.is_authenticated()


def auth_logout(request):
    logout(request)
    return request.user.is_authenticated()


def list_user(request):
    users = trans_data(serializers.serialize("json", User.objects.all()))
    return HttpResponse(users)

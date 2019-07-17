from django.contrib.auth.models import User, Group
from django.http import HttpResponseForbidden

from ruleManage.models import Right
from ruleManage.ser import RightSer


def get_user_rights(user: User) -> list:
    """获取指定用户的所有权限
    request.user"""
    query = Right.objects.filter(group_set__user=user).distinct()
    return RightSer(query, many=True).data()
    # 返回结果
    # [
    #     {'id': 4, 'name': '权限2', 'describe': '测试用的', 'key': 'r4'},
    #     {'id': 6, 'name': '权限2', 'describe': '测试用的', 'key': 'r6'},
    #     {'id': 7, 'name': '权限1', 'describe': '测试用的', 'key': 'r7'},
    #     {'id': 1, 'name': '权限1', 'describe': '测试用的', 'key': 'r1'},
    #     {'id': 2, 'name': '权限2', 'describe': '测试用的', 'key': 'r2'}
    # ]


# 获取组权限列表
# grouplst = Group.objects.prefetch_related('right_set')
#
# RightSer(obj.right_set.all(), many=True).data()


def right_required(right_key_lst=()):
    """权限验证装饰器(必须拥有right_key_lst中的全部权限才能通过验证)
    @right_required(['权限1', '权限2'])"""

    def decorator(func):
        def wrapper(request):
            right_lst = tuple(map(lambda item: item.get('key'), get_user_rights(request.user)))
            for rig in right_key_lst:
                if rig not in right_lst:
                    return HttpResponseForbidden('权限不足!')
            return func(request)

        return wrapper

    return decorator


def right_or_required(right_key_lst=()):
    """权限验证装饰器(只要有right_key_lst中的一个权限即可通过验证)
    @right_required(['权限1', '权限2'])"""

    def decorator(func):
        def wrapper(request):
            right_lst = tuple(map(lambda item: item.get('key'), get_user_rights(request.user)))
            for rig in right_key_lst:
                if rig in right_lst:
                    return func(request)
            return HttpResponseForbidden('权限不足!')

        return wrapper

    return decorator

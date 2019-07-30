import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transfer.settings")
django.setup()
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from ruleManage.right_tools import *
from ruleManage.ser import RightSer
from datamoving.public_params import *
from ruleManage.serializers import *
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from datetime import datetime


@api_view(['GET'])
def rule_delete(request):
    """删除规则?ids=1,2,3,4
    状态 1  表示删除成功
        2  规则在使用，无法删除
        0  删除失败
    """
    rids = request.GET.get('id')
    ids = rids.split(',')
    if not rids:
        return Response(status.HTTP_400_BAD_REQUEST)
    for rid in ids:
        count = Task.objects.filter(rule_id=rid).count()  # 验证要删除的规则在任务中是否有被使用
        if count > 0:
            print("规则正在任务中使用，无法删除！")
            return Response(EXIST)
        else:
            rule = Regulation.objects.filter(id=rid)
            path = rule.values('rule_template')[0]['rule_template']
            result = rule.delete()
            if result[0]:
                print("成功删除！")
                # 删除相关文件
                if path:
                    os.remove(path)
                return Response(SUCCESS)
            else:
                print('删除失败')
                return Response(ERROR)


@api_view(['GET'])
def rule_list(request):
    """查找规则信息，分页展示"""
    dic = {}
    rule_name = request.GET.get('rule_name')

    # 规则名称查询
    if rule_name:
        dic['rule_name__contains'] = rule_name
    # 所属系统查询
    belong_sys = request.GET.get('belong_sys')
    if belong_sys:
        dic['belong_sys'] = belong_sys
    # 创建时间查询
    create_time1 = request.GET.get('create_time_gte')
    create_time2 = request.GET.get('create_time_lte')
    if create_time1 and create_time2:
        dic['create_time__range'] = (
            datetime.strptime(create_time1, '%Y-%m-%dT%H:%M:%S'),
            datetime.strptime(create_time2, '%Y-%m-%dT%H:%M:%S')
        )
    regulation = Regulation.objects.filter(**dic).order_by('-id')
    page = ListPage2()
    page_roles = page.paginate_queryset(queryset=regulation, request=request)
    roles_ser = RegulationListSerializer(instance=page_roles, many=True)
    # 获取总条数和总页数
    size_count = regulation.count()
    size = int(request.GET.get('size') or ListPage2.page_size)
    return Response({
        'size_count': size_count,
        'page_count': int((size_count + size - 1) / size),  # 向上取整
        'results': roles_ser.data,
    })


@api_view(['GET'])
def rule_detail(request):
    """获取单个规则的详细信息"""
    rid = request.GET.get('id')
    #task_type=0归档  task_type=1回灌
    task_type = request.GET.get('task_type')
    res = 1
    if task_type != None:
    #创建新任务时，如果相同规则下有失败的任务，必须先将失败的任务处理完，才可以创建新任务,跟回灌任务不冲突
        count = Task.objects.filter(task_type=task_type).count()
        if count > 0:
            task = Task.objects.filter(task_type=task_type).order_by('-id')[0]
            rule_id = Regulation.objects.get(id=rid).id
            if task.status == 2 and task.rule_id == rule_id and int(task.task_type) == int(task_type):
                print('不能创建')
                res = 0
    if not rid:
        return Response(status.HTTP_400_BAD_REQUEST)
    try:
        rule = Regulation.objects.get(id=rid)
    except Regulation.DoesNotExist:
        return Response(status.HTTP_404_NOT_FOUND)
    roles_ser = RegulationDetailSerializer(rule)
    roles_next = {
        "rule": roles_ser.data,
        "next": res
    }
    return Response(roles_next)


def upload_rule_temp(file):
    """上传规则模板"""
    timestamp = datetime.strftime(datetime.now(), '%Y%m%d%H%M%S')
    new_file_name = timestamp + file.name  # 将上传的文件名前添加上当前的时间，以免造成重名
    f = open(os.path.join(PUBLIC_DIR(), new_file_name), 'wb')
    for chunk in file.chunks(chunk_size=1024):
        f.write(chunk)
    f.close()
    return new_file_name


@api_view(['POST'])
def rule_add(request):
    """获取前台表单内的数据,添加到数据库"""
    _rule = dict(request.data)
    if not _rule:
        return Response("无数据!")
    count = Regulation.objects.filter(rule_name=_rule['rule_name']).count()

    if count > 0:
        return Response(EXIST)
    try:
        file_name = upload_rule_temp(_rule['template'][0])
        del _rule['template']
        _rule['rule_template'] = PUBLIC_DIR() + file_name
        for key, value in _rule.items():
            if key != 'rule_template':
                _rule[key] = value[0]
                if _rule['describe'] == 'undefined':
                    _rule[key] = ''
        _rule['create_user'] = 'admin'
        Regulation.objects.create(**_rule)
    except Exception as err:
        print(err)
        return Response(ERROR)
    return Response(SUCCESS)


@api_view(['POST'])
def rule_update(request):
    """规则的修改"""
    print('规则的修改')
    _rule = dict(request.data)
    if not _rule:
        return Response(status.HTTP_400_BAD_REQUEST)
    # 系统校验规则名称不能重复
    try:
        if _rule['template'][0] == 'undefined':
            del _rule['template']
        else:
            # 删除原有规则
            rule = Regulation.objects.filter(id=_rule['id'][0])
            path = rule.values('rule_template')[0]['rule_template']
            if path:
                os.remove(path)
            # 创建新规则并保存到数据库
            file_name = upload_rule_temp(_rule['template'][0])
            del _rule['template']
            _rule['rule_template'] = PUBLIC_DIR() + file_name
        for key, value in _rule.items():
            if key != 'rule_template':
                _rule[key] = value[0]
        Regulation.objects.filter(id=_rule['id']).update(**_rule)
    except BaseException as e:
        print(e)
        return Response(ERROR)
    return Response(SUCCESS)


@login_required
@right_or_required(['r2', 'r1'])
@api_view(['GET'])
def right_list(request):
    """获取权限列表"""
    try:
        return Response(RightSer(Right.objects.all(), many=True).data())
    except Exception as err:
        return Response(str(err), status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def right_change(request):
    """修改权限
    {
        group_id: 1,
        right_set: [1,2,3,4],
    }"""
    try:
        g = Group.objects.get(id=request.data.get('group_id'))
        g.right_set.clear()
        g.right_set.add(*request.data.get('right_set'))
        g.save()
        return Response('OK')
    except Exception as err:
        return Response(str(err), status=status.HTTP_400_BAD_REQUEST)


if __name__ == '__main__':
    task = Task.objects.filter(rule_id=59)[-1]
    print(task.task_name)
    pass


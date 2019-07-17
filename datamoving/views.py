import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transfer.settings")
django.setup()
from datetime import date
from django.db.models import Count, Sum, F
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from datamoving.serializers import *
from datamoving.service import *
import threading
from environment.models import App
from datamoving.models import Regulation, Task
from datamoving.loop_time import *
from datamoving.public_params import *
from rest_framework.throttling import UserRateThrottle


logg = logging.getLogger('autoops')


def get_user_info(req, func):
    logg.info(req.META['REMOTE_ADDR'])
    logg.info(req.META['USERNAME'])
    logg.info(req.user)
    logg.info(func.__name__)


@api_view(['GET'])
def task_list(request):

    # get_user_info(request, task_list)
    """作业列表
    ?size=10&page=1&task_name=xxx&status=xxx&create_time1=xxx&create_time2=xxx&run_way=xxx&task_type=0&index=1
    ?create_time1=2019-05-05%2011:10:57&create_time2=2019-05-05%2011:10:59  按时间查询
    ?limit=5&status=1&index=1  主页(执行中) index=1表示最近24小时
    ?status=3&index=1  主页(执行成功) index=1表示最近24小时
    ?task_type=1  获取回灌数据列表"""
    dic = {}
    # 作业名查询
    task_name = request.GET.get('task_name')
    if task_name:
        dic['task_name__icontains'] = task_name
    # 作业状态查询
    status = request.GET.get('status')
    if status:
        dic['status'] = status
    # 创建时间查询
    create_time1 = request.GET.get('create_time_gte')
    create_time2 = request.GET.get('create_time_lte')
    if create_time1 and create_time2:
        dic['create_time__range'] = (
            datetime.strptime(create_time1, "%Y-%m-%dT%H:%M:%S"),
            datetime.strptime(create_time2, "%Y-%m-%dT%H:%M:%S"))
    # 执行方式查询
    run_way = request.GET.get('run_way')
    if run_way:
        dic['run_way'] = run_way
    # 迁移还是回灌
    task_type = request.GET.get('task_type')
    dic['task_type'] = 0 if not task_type else task_type
    # 是否是主页初始化数据
    index = request.GET.get('index')
    if index:
        del dic['task_type']
        # 列表
        dic['start_time__gte'] = datetime.now() - timedelta(days=1)
        roles = Task.objects.only(*TaskListSer.Meta.fs).filter(**dic).order_by('-id')
        roles_ser = TaskListSer(roles, many=True)
        del dic['status']
        task_count_dic = {1: 0, 2: 0, 3: 0}
        task_count_lst = Task.objects.only('status').filter(**dic).values('status').annotate(
            count=Count('status')).order_by('status')
        for t in task_count_lst:
            task_count_dic[t['status']] = t['count']
        return Response({
            'tasks': roles_ser.data,
            'task_count': task_count_dic,
        })
    roles = Task.objects.only(*TaskListSer.Meta.fs).filter(**dic).order_by('-id')
    page = ListPage2()
    page_roles = page.paginate_queryset(queryset=roles, request=request)
    roles_ser = TaskListSer(instance=page_roles, many=True)
    # 获取总条数和总页数
    size_count = roles.count()
    size = int(request.GET.get('size') or ListPage2.page_size)
    return Response({
        'size_count': size_count,
        'page_count': int((size_count + size - 1) / size),  # 向上取整
        'results': roles_ser.data,
    })


@api_view(['GET'])
def task_detail(request):
    """作业详细信息
    ?id=1"""
    idi = request.GET.get('id')

    # #创建新任务时，如果相同规则下有失败的任务，必须先将失败的任务处理完，才可以创建新任务
    # task = Task.objects.order_by('-id')[0]
    # rule_id = Regulation.objects.get(id=dic['rule_id']).id
    # if task.status == 2 and task.rule_id == rule_id:
    #     print('不能创建')
    #     return Response('本规则下有失败的任务，请先处理完再创建新的任务')

    if not idi:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    try:
        app = Task.objects.get(id=idi)
    except Exception as err:
        return Response(str(err), status=status.HTTP_404_NOT_FOUND)
    roles_ser = TaskDetailSer(app)
    return Response(roles_ser.data)


@api_view(['GET'])
def task_add(request):

    """添加作业初始化获取数据源和规则"""
    # print('task_add')
    # task = Task.objects.order_by('-id')[0]
    # status = Task.objects.get(id=task.id).status
    # print(status)
    # if status != 3:
    #     print('必须将上一次的任务执行完！')
    #     data_dict = {
    #         'rules':'必须将上一次的任务执行完'
    #     }
    #     return Response(data_dict)
    data_dict = {}
    datasources = get_datasources()
    rules = get_rule_info()
    data_dict['rules'] = rules
    data_dict['db_sources'] = datasources
    return Response(data_dict)


@api_view(['POST'])
def task_save(request):
    # get_user_info(request, task_save)
    """添加作业"""
    print('task_save')
    dic = request.data
    # #创建新任务时，如果相同规则下有失败的任务，必须先将失败的任务处理完，才可以创建新任务
    # task = Task.objects.order_by('-id')[0]
    # rule_id = Regulation.objects.get(id=dic['rule_id']).id
    # if task.status == 2 and task.rule_id == rule_id:
    #     print('不能创建')
    #     return Response('本规则下有失败的任务，请先处理完再创建新的任务')
    if not dic['task_name']:
        return Response(ERROR)
    try:
        # 创建任务时直接创建日志
        if not dic['start_time']:
            del dic['start_time']
        try:
            if not dic['total_count']:
                # del dic['total_count']
                pass
        except Exception as e:
            print(e)
        time_to_create_execute(dic)
    except django.db.utils.IntegrityError as err:
        return Response(EXIST)
    except Exception as err:
        # raise err
        print(err)
        return Response(ERROR)
    return Response(SUCCESS)


@api_view(['GET'])
def update_before(request):
    """更新前数据初始化"""
    data_dict = {}
    id = request.GET.get('id')

    task = list(Task.objects.filter(id=id).values())[0]
    data_dict['task'] = task
    return Response(data_dict)


@api_view(['POST'])
def task_update(request):
    # get_user_info(request, task_update)
    """更新"""
    dic = request.data
    try:
        # 创建任务时直接创建日志
        if not dic['start_time']:
            del dic['start_time']
        dic['time_rule'] = json.dumps(dic['time_rule']) if type(dic['time_rule']) == dict else dic['time_rule']
        Task.objects.filter(id=dic['id']).update(**dic)
        if dic['run_way'] == 1:
            if get_time(dic['id']):
                result = rem_time(dic['id'])
                print(result, '删除定时')
                add = cron_time(create_execute, dic, dic['id'], dic['time_rule'],
                                dic['start_time'])
            else:
                add = cron_time(create_execute, dic, dic['id'], dic['time_rule'],
                                dic['start_time'])
        else:
            if get_time(dic['id']):
                result = rem_time(dic['id'])
                print(result, '删除定时')
            else:
                print('当前定时器没有执行！')
                pass
    except Exception as err:
        raise err
    return Response(SUCCESS)


@api_view(['GET'])
def task_delete(request):
    # get_user_info(request, task_delete)
    """删除作业?ids=1,2,3,4,5"""
    ids_str = request.GET.get('ids')
    ids = ids_str.split(',')
    if not ids_str:
        Response(ERROR)
    try:
        for id in ids:
            Task.objects.filter(id=id).delete()
            if get_time(id):
                result = rem_time(id)
                print(result, '删除定时器')
    except Exception as err:
        Response(ERROR)
    return Response(SUCCESS)


@api_view(['GET'])
def task_log(request):
    """作业日志
    ?id=1"""
    id = request.GET.get('id')
    if not id:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    try:
        info = {}
        task = Task.objects.only(*LogInit.Meta.fs).filter(id=id).first()
        task_data = LogInit(task)
        info['task'] = task_data.data
        info['logs'] = Log.objects.get(task_id=id).content
    except Exception as err:
        raise err
    return Response(info)


@api_view(['GET'])
def task_run(request):
    # get_user_info(request, task_run)
    """作业批量执行
    ?ids=1,2,3,4"""
    ids = request.GET.get('ids')
    man_f = True if request.GET.get('continue') else False
    id_list = ids.split(',')
    if not ids:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    for id in id_list:
        run_status = Task.objects.get(id=id).status
        if run_status == 1:
            print("执行状态为执行中,无法进行执行")
            pass
        else:
            task = Task.objects.get(id=id)
            threading.Thread(target=execute_task, args=(task, man_f)).start()
    return Response('OK')


FIELD1 = 'sum_commit'  # 图表数据字段1迁移数据
FIELD2 = 'sum_delete'  # 图表数据字段2删除数据


@api_view(['GET'])
def task_index_num(request):
    """总览页初始化数据"""
    # 数量
    dic = {
        'cards': {
            **Task.objects.filter(status=3).aggregate(task_count=Count('id')),
            'actual_sum': Task.objects.filter(status=3).aggregate(actual_sum=Sum(FIELD1))['actual_sum'] or 0,
            **Regulation.objects.aggregate(rule_count=Count('id')),
            **App.objects.aggregate(db_count=Count('id')),
        }
    }
    # 列表
    idic = {
        'status': 3,
        'start_time__gte': datetime.now() - timedelta(days=1),
    }
    roles = Task.objects.only(*TaskListSer.Meta.fs).filter(**idic).order_by('-id')
    roles_ser = TaskListSer(roles, many=True)
    dic['tasks'] = roles_ser.data
    del idic['status']
    task_count_dic = {1: 0, 2: 0, 3: 0}
    task_count_lst = Task.objects.only('status').filter(**idic).values('status').annotate(
        count=Count('status')).order_by('status')
    for t in task_count_lst:
        task_count_dic[t['status']] = t['count']
    dic['task_count'] = task_count_dic
    # 图表
    today = datetime.now().date()
    select = {'time': 'DATE_FORMAT(start_time, "%%w")'}
    dic['bar_chart'] = Task.objects.filter(start_time__gte=today - timedelta(days=today.weekday())).extra(
        select=select).values('time').annotate(es_sum=Sum(FIELD1), ac_sum=Sum(FIELD2)).order_by('time')
    # 饼图
    dic['pie_chart'] = Task.objects.values('rule_id', 'rule__rule_name').annotate(
        name=F('rule__rule_name'), value=Count('id')).values(
        'rule_id', 'name', 'value').order_by('-value', 'name')[:10]
    return Response(dic)


@api_view(['GET'])
def task_index_chart(request):
    """总览页图表部分
    ?type=hour/weeks/days/month&rule_id 天/周/月/年"""
    itype = request.GET.get('type')
    today = datetime.now().date()
    idic = {}
    rule_id = request.GET.get('rule_id')
    if rule_id == 'null':
        idic['rule_id__isnull'] = True
    elif rule_id:
        idic['rule_id'] = rule_id
    if itype == 'hour':
        select = {'time': 'DATE_FORMAT(start_time, "%%k")'}
        idic['start_time__gte'] = today
    elif itype == 'weeks':
        select = {'time': 'DATE_FORMAT(start_time, "%%w")'}
        idic['start_time__gte'] = today - timedelta(days=today.weekday())
    elif itype == 'days':
        select = {'time': 'DATE_FORMAT(start_time, "%%e")'}
        idic['start_time__gte'] = today - timedelta(days=today.day - 1)
    else:
        select = {'time': 'DATE_FORMAT(start_time, "%%c")'}
        idic['start_time__gte'] = date(year=today.year, month=1, day=1)
    dic = Task.objects.filter(**idic).extra(select=select).values('time').annotate(
        es_sum=Sum(FIELD1), ac_sum=Sum(FIELD2)).order_by('time')
    return Response(dic)


@api_view(['GET'])
def get_next_time(request):
    """
    根据id获取定时任务(暂未使用)
    :param request:
    :return:
    """
    time_rule = get_time(request.GET.get('id'))
    print(time_rule)
    return Response(SUCCESS)


@api_view(['GET'])
def get_next_count(request):
    #(request, get_next_count)

    """
    根据前端请求获取表的预统计数量
    :param request:
    :return:
    """
    task = Task.objects.filter(id=request.GET.get('id')).first()
    if not task:
        return Response('作业不存在', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    source_id = task.source_id
    source = pass_decode(source_id)
    conn_curs, curs = oracle_connect(source)
    conn = create_conn(LINUX_IP(), LINUX_USER(), LINUX_PASS())
    tables, table_names = get_table_info(task.rule_id)
    # 获取规则中所涉及的表
    sh_path = get_sh_path(task.rule_id)
    table_info = {}
    # 查询所有数据
    if task.task_type and task.rollback_condition:
        sql_list = execute_sh(conn, table_names, 'no', source['db_username'], 'no', '0', sh_path,
                              RB_CONDITION=task.rollback_condition)
    else:
        sql_list = execute_sh(conn, table_names, 'no', source['db_username'], 'no', '0', sh_path)
    '''
    max_id = get_max_values(conn, curs, table_names, source, sh_path)
    command = "sh %s %s %s %s %s %s %s %s %s %s %s %s" % \
              (sh_path, sh_type('0'), table_names, 'no', source['db_username'], '0', 'N', 'N', 'N', 'N', max_id, 'N')
    '''
    # 有一个时间重复的问题，明天看

    for i in range(sql_list.__len__()):
        if tables[i] in sql_list[i]:
            # curs.prepare()
            values = curs.execute(sql_list[i])
            table_info[tables[i]] = values.fetchall()[0][0]
    curs.close()
    conn.close()
    conn_curs.close()
    task.estimate_count = json.dumps(table_info)
    task.save()
    return Response(json.dumps(table_info))


@api_view(['GET'])
def get_all_timing(request):
    """
    获取全部定时任务,暂未使用
    :param request:
    :return:
    """
    jobs = get_all()
    return Response(str(jobs))


class OncePerDayUserThrottle(UserRateThrottle):
    rate = '1/minute'


@api_view(['GET', 'POST'])
@throttle_classes([OncePerDayUserThrottle])
def hello_world(request):
    if request.method == 'POST':
        return Response({"message": "Got some data!", "data": request.data})
    return Response({"message": "Hello, world!"})


if __name__ == '__main__':
    task = Task.objects.get(id=1221)
    task.actual_count = None
    task.save()
    # for k, v in actual_count.items():
    #     print(k, 'k')
    #     print(type(v), 'v')

    # task = {"HTIC_QUOTE_PROCESSING_LOG": 50, "HTIC_QUOTE_PROCESSING_LOG_RULE": 0}
    # for k, v in task.items():
    #     print(v)
    # import math
    # task = Task.objects.get(id=738)
    # total_count = int(task.total_count)
    # commit_count = int(task.commit_count)
    # print(total_count, commit_count)
    # print(math.ceil(18/5))
    # actual_count = list(Task.objects.filter(id=716).values('estimate_count'))
    # dic = {}
    # print(actual_count)
    # for count in actual_count:
    #     for k, v in dic.items():
    #         print(list(eval(v).values()))
    #         print(sum(list(eval(v).values())))
    pass
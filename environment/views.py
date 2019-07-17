import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transfer.settings")
django.setup()
import traceback
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from environment.con_oracle import oracle_connect
from environment.serializers import *
from environment.service import *
from environment.models import DataSet, App
from django.http import HttpResponse
from datamoving.public_params import *
from environment.passwd_tool import AESCrypto
from datamoving.loop_time import *


@api_view(['GET'])
def data_list(request):
    """数据源列表
    ?limit=2&offset=0&info=225&belong_sys_id=1
    ?info=xx&belong_sys_id=xx"""
    info_dict = dict(request.GET.items())
    # dic = {(k + '__icontains' if k == 'info' else k): v for k, v in request.GET.items() if k in ['info', 'belong_sys_id']}

    belong = info_dict['belong_sys_id']
    del info_dict['belong_sys_id']
    ids = get_select_ids(info_dict)
    if belong:
        roles = App.objects.only(*DataSourceSer.Meta.fs).filter(id__in=ids).filter(belong_sys=belong).order_by('-id')
    else:
        roles = App.objects.only(*DataSourceSer.Meta.fs).filter(id__in=ids).order_by('-id')

    page = ListPage2()

    page_roles = page.paginate_queryset(queryset=roles, request=request)
    roles_ser = DataSourceSer(instance=page_roles, many=True)
    # 获取总条数和总页数
    size_count = roles.count()
    size = int(request.GET.get('size') or ListPage2.page_size)
    all_sys = DataSet.objects.all().values('id', 'name')
    return Response({
        'size_count': size_count,
        'page_count': int((size_count + size - 1) / size),  # 向上取整
        'count': roles.count(), 'results': roles_ser.data, "sys": all_sys
    })



@api_view(['GET'])
def data_detail(request):
    """数据源详细信息
    ?id=1"""
    idi = request.GET.get('id')
    if not idi:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    try:
        app = App.objects.get(id=idi)
    except Exception as err:
        return Response(str(err), status=status.HTTP_404_NOT_FOUND)
    roles_ser = DataSourceSer(app, m_flag=True)
    return Response(roles_ser.data)


@api_view(['POST'])
def data_add(request):
    """添加数据源
    """
    try:
        info = {}
        dic = request.data
        # 判断名字是否存在
        contents = list(App.objects.all().values('info'))
        for content in contents:
            if json.loads(content['info'])['datasource_name'][0] == dic['datasource_name']:
                return EXIST
        # 不存在就保存
        for key in dic.keys():
            if key in list(DATA_SOURCE.keys()):
                if 'password' in key:
                    info[key] = [str(AESCrypto.encrypt(dic[key])), DATA_SOURCE[key]]
                else:
                    info[key] = [dic[key], DATA_SOURCE[key]]
        App.objects.create(belong_sys_id=dic['belong_sys_id'], typer=dic['db_type'],
                           info=json.dumps(info, ensure_ascii=False))
    except Exception as err:
        return Response(ERROR)
    return Response(SUCCESS)


@api_view(['GET'])
def datasource_init(request):
    """数据源初始数据
    """
    sys_names = list(DataSet.objects.all().values('id', 'name'))
    try:
        data = {"belong_syses": sys_names, "db_types": App.mod}
    except Exception as err:
        raise err
    return Response(data)


@api_view(['POST'])
def data_update(request):
    """添加数据源
    """
    try:
        info = {}
        dic = request.data
        print(dic)
        # 不存在就保存
        for key in dic.keys():
            if key in list(DATA_SOURCE.keys()):
                if 'password' in key:
                    info[key] = [str(AESCrypto.encrypt(dic[key])), DATA_SOURCE[key]]
                elif 'id' is key:
                    pass
                else:
                    info[key] = [dic[key], DATA_SOURCE[key]]
        print(dic['id'], dic['belong_sys_id'], dic['db_type'], json.dumps(info, ensure_ascii=False))
        App.objects.filter(id=dic['id']).update(belong_sys_id=dic['belong_sys_id'], typer=dic['db_type'],
                                                info=json.dumps(info, ensure_ascii=False))
    except Exception as err:
        raise err
        # return Response(ERROR)
    return Response(SUCCESS)


@api_view(['GET'])
def data_delete(request):
    """删除数据源
    ?id=1"""
    print('test')
    idi = request.GET.get('id')
    if not idi:
        return Response(ERROR)
    try:
        App.objects.filter(id=idi).delete()
    except Exception as err:
        return Response(ERROR, status=status.HTTP_501_NOT_IMPLEMENTED)
    return Response(SUCCESS)


@api_view(['GET'])
def data_test(request):
    """测试数据源?id=1"""
    datesource_id = request.GET.get('id')
    if not datesource_id:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    source = pass_decode(datesource_id)
    t_conn_curs, t_curs = oracle_connect(source)
    if t_curs != 'failed':
        return Response(SUCCESS)
    else:
        return Response(ERROR)


@api_view(['POST'])
def index_main(request):
    """总览页面的数据"""
    data = {
        'cards': {
            'task_count': successful_task_count(),  # 已完成归档任务条数 执行成功3
            'total_count': successful_data_count(),  # 归档成功,状态为3(执行成功)的所有数据笔数
            'rule_count': rules_count(),  # 查询当配置的所有规则数
            'sources_count': sources_count(),  # 查询当前配置的所有数据源
        },
        'tasks_24hours': task_24hours(),  # 获取二十四小时内任务执行
        'precent_list': get_rule_id(),  # 统计规则占比
    }

    print(data, 'data')
    return HttpResponse(json.dumps(data))


def get_select_ids(data):
    all_values = App.objects.all().values('info', 'id')
    changdu = ''
    for leng in data.values():
        changdu += leng
    if changdu.__len__() == 0:
        return [a['id'] for a in all_values]
    name_list = []
    ip_list = []
    server_list = []
    for info in all_values:
        name_list.append([info['id'], json.loads(info['info'])['datasource_name'][0]])
        ip_list.append([info['id'], json.loads(info['info'])['ip'][0]])
        server_list.append([info['id'], json.loads(info['info'])['server_name'][0]])
    one = []
    two = []
    three = []
    for info in range(name_list.__len__()):
        for k, v in data.items():
            if data['datasource_name'] in name_list[info][1] and data['datasource_name'] != '':
                one.append(name_list[info][0])
            if data['ip'] in ip_list[info][1] and data['ip'] != '':
                two.append(ip_list[info][0])
            if data['server_name'] in server_list[info][1] and data['server_name'] != '':
                three.append(server_list[info][0])
    one = list(set(one))
    two = list(set(two))
    three = list(set(three))
    xx = []
    vv = [x for x in data.values() if x != '']
    if (one and two and three) or len(vv) == 3:
        xx = [x for x in one if x in two and x in three]
    elif one and two and len(vv) == 2:
        xx = [x for x in one if x in two]
    elif one and three and len(vv) == 2:
        xx = [x for x in one if x in three]
    elif two and three and len(vv) == 2:
        xx = [x for x in two if x in three]
    elif one and len(vv) == 1:
        xx = one
    elif two and len(vv) == 1:
        xx = two
    elif three and len(vv) == 1:
        xx = three
    else:
        xx = xx
    return xx



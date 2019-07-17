import json

from config.serializers import ConfigListSer, ListPage2, ConfigDetailSer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from config.models import Config
from datamoving.public_params import *

@api_view(['GET'])
def config_list(request):
    # dic = request.data
    # if not dic:
    #     return Response(status.HTTP_400_BAD_REQUEST)
    try:
        configs = Config.objects.all().order_by('-id')
        page = ListPage2()
        page_roles = page.paginate_queryset(queryset=configs, request=request)
        config_ser = ConfigListSer(instance=page_roles, many=True)
        # 获取总条数和总页数
        size_count = configs.count()
        size = int(request.GET.get('size') or ListPage2.page_size)
    except Exception as e:
        return Response(ERROR)
    return Response({
        'size_count': size_count,
        'page_count': int((size_count + size - 1) / size),  # 向上取整
        'results': config_ser.data,
    })


@api_view(['GET'])
def config_detail(request):
    """传入id 查询相关的config信息"""

    config_id = request.GET.get('id')
    if not config_id:
        return Response(status.HTTP_400_BAD_REQUEST)

    config_ser = ConfigDetailSer(Config.objects.get(id=config_id))
    return Response(config_ser.data)


@api_view(['POST'])
def config_add(request):
    """传入id 查询相关的config信息"""
    dic = request.data
    if request.method == "GET" or not dic:
        return Response(status.HTTP_400_BAD_REQUEST)
    try:

        for config in json.loads(dic['results']):
            Config.objects.filter(id=config['id']).update(**config)
    except Exception as e:
        print(e)
        return Response(ERROR)
    return Response(SUCCESS)


@api_view(['GET'])
def config_delete(request):
    """传入id 查询相关的config信息"""
    dic = request.data
    if request.method == "POST" or not dic:
        return Response(status.HTTP_400_BAD_REQUEST)
    try:
        Config.objects.filter(dic['id']).delete()
    except Exception as e:
        return Response(ERROR)
    return Response(SUCCESS)
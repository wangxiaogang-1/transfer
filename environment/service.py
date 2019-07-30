#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transfer.settings")
django.setup()
import json




from django.db.models import Q
from datamoving.models import *
from environment.models import *
from django.db.models import Count

from datetime import datetime, timedelta
from environment.passwd_tool import *

'''返回所有数据源信息'''


def get_datasources():
    # 获取id为0的数据源
    """
    获取所有数据源数据
    :return:
    """
    list_datasource = []
    datasources = list(App.objects.filter(typer=0).values())
    for datasource in datasources:
        data = {}
        info = json.loads(datasource['info'])
        data['id'] = datasource['id']
        data['datasource_name'] = info['datasource_name'][0]
        list_datasource.append(data)
    return list_datasource


def get_rule_info():
    rules = Regulation.objects.all().values('id', 'rule_name')
    rule_list = []
    for rule in rules:
        rule_list.append(rule)
    return rule_list

'''数据库密码加密'''

def pass_encode(datasource_id):
    """
    传入数据源配置信息,根据password字段进行加密。格式不做改变
    :return:
    """
    info = list(App.objects.filter(id=datasource_id).values('info'))[0]['info']
    print(info)
    data_dict = json.loads(info)
    for key, value in data_dict.items():
        if 'password' in key:
            value[0] = str(AESCrypto.encrypt(value[0]))
        data_dict[key] = value
    print(data_dict)
    App.objects.filter(id=datasource_id).update(info=json.dumps(data_dict, ensure_ascii=False))


'''数据库解密'''
def pass_decode(datasource_id):
    """
    传入数据源配置信息,根据password字段进行解密。格式修改成dict 一层关系
    :param info:
    :return:
    """
    app = App.objects.get(id=datasource_id)
    info = app.info
    data_dict = json.loads(info)
    for key, value in data_dict.items():
        if 'password' in key:
            value[0] = str(AESCrypto.decrypt(AESCrypto.doing(value[0])))
        data_dict[key] = value
    new_dict = {}
    for key, value in data_dict.items():
        new_dict[key] = value[0]
    return new_dict


'''返回单条数据源'''

def get_datasource(id):
    """
    根据数据源id查询数据源信息
    :return:
    """

    info = App.objects.get(id=id).info

    data_dict = json.loads(info)

    return data_dict


'''总览页顶部功能'''


# 已完成归档任务条数 执行成功3
def successful_task_count():
    """
    归档成功,状态为3(执行成功)的任务数量
    :return:
    """
    successful_count = Task.objects.filter(status=3).count()
    return successful_count


# 已完成归档数据笔数
def successful_data_count():
    """
    归档成功,状态为3(执行成功)的所有数据笔数
    :return:
    """
    all_count = list(Task.objects.filter(status=3).values('actual_count'))
    return calculate_num(all_count, 'actual_count')


# 计算归档字段笔数
def calculate_num(all_count, field):
    """
    :param all_count:list(query_set)类型的统计数据
    :param field: values(field)类型的字段
    :return: 返回所有数据相加之和(只适用于这样格式的数据{"table1":12345,"table2":321,"table3":100})
    """
    num = 0
    for data in all_count:
        one_data = json.loads(data[field])
        for key, value in one_data.items():
            num += value
    return num


# 已有规则数量
def rules_count():
    """
    查询当配置的所有规则数
    :return:
    """
    total = Regulation.objects.all().count()
    return total


# 已有配置源数量
def sources_count():
    '''
    查询当前配置的所有数据源
    :return:
    '''
    sources = App.objects.filter(typer=0).count()
    print(sources)
    return sources


# 获取二十四小时内任务执行
def task_24hours():
    """
    condition: 根据前台传递
    :return: 返回根据不同条件查询，并且时间在24小时之内的任务数据
    """
    condition = {"status": 0}
    now, yesterday = get_format_time(1)
    tasks = Task.objects.filter(Q(start_time__lte=now) & Q(start_time__gte=yesterday) & Q(**condition))
    return tasks


# 获取当前时间和自定义时间
def get_format_time(day, interval=1):
    """
    :param day: 获取几天的数据
    :param interval: 查询间隔
    :return: 返回当前时间(后)，和根据间隔查询的开始时间(前)
    """
    tm = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # str
    now = datetime.strptime(str(tm), "%Y-%m-%d %H:%M:%S")  # datetime.datetime
    last_day = now - timedelta(days=day * interval)
    print(now, last_day)
    # 转换为时间戳
    # new_now = now.timestamp()
    # new_yesterday = last_day.timestamp()
    # 因为数据库中存储的是Integer类型
    return now, last_day


# 根据起止时间获取列表
def show_start_end(start, end, interval=1):
    """
    :param start: 开始时间(timestamp类型)
    :param end: 结束时间(timestamp类型)
    :param interval: (间隔，默认为一天)
    :return: 返回根据间隔分割的时间列表(timestamp类型)
    """
    # 开始时间
    # 结束时间
    # 代表间隔天数
    time_list = []
    start = start.timestamp()
    end = end.timestamp()
    total = (int(end) - int(start)) // 86400 * interval
    if total == 0:
        total = 2
    for i in range(total):
        time_list.append(datetime.fromtimestamp(end))
        end -= 86400 * interval
        if end == start:
            time_list.append(datetime.fromtimestamp(end))
            break
    time_list.reverse()
    print(time_list)
    return time_list


# 每月预估数据和实际数据对比
def estimate_actual_compare(num, interval):
    """
    :param num: 查询时需要取几次数据
    :param interval: 查询的间隔(单位)天
    :return: 返回值包含(迁移成功的任务数,预估值总量,实际值总量)
    """
    # interval = 30
    # 前面是取多少次数据，后的的参数是按多久进行划分
    now, yesterday = get_format_time(num, interval)
    month_count = []
    # 这里的最后一个参数是间隔
    for i in show_start_end(yesterday, now, interval)[1:]:
        print(i, 'iii')
        count_dict = {}
        tasks = list(Task.objects.filter(Q(status=3) & Q(start_time__lte=i) & Q(start_time__gte=i - timedelta(days=1))). \
                     values('estimate_count', 'actual_count'))
        count_dict['count'] = tasks.__len__()
        count_dict['estimate'] = calculate_num(tasks, 'estimate_count')
        count_dict['actual'] = calculate_num(tasks, 'actual_count')
        month_count.append(count_dict)
    print(month_count)
    return month_count


# 通过规则id查询规则名称
def get_rule_name(rule_id):
    """
    :param rule_id:传入规则id
    :return: 返回规则名称
    """
    return Regulation.objects.get(id=rule_id).rule_name


def get_rule_id():
    """
    统计规则占比
    :return: 列表类型,rule_name:规则名称 percent:归档任务规则占比

    """
    # total = Task.objects.all().count()
    percent_list = []
    tasks = list(Task.objects.all().values('rule_id').annotate(count=Count('rule_id')))
    for task in tasks:
        proportion_dict = {'name': get_rule_name(task['rule_id']), 'value': task['count']}
        percent_list.append(proportion_dict)
    print(percent_list)
    return percent_list



if __name__ == '__main__':

    i = "20190729000000"
    # tasks = list(Task.objects.filter(Q(status=3) & Q(start_time__gte="2019-07-29 00:00:00")).values('estimate_count', 'actual_count'))
    tasks = list(Task.objects.filter(Q(status=3) & Q(start_time__lte=i) & Q(start_time__gte=i - timedelta(days=1))). \
                 values('estimate_count', 'actual_count'))
    print(tasks, 'tasks')

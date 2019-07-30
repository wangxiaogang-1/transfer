import hashlib
import re
import time
import math
import logging
import traceback
from django.http import HttpResponse
from environment.service import *
from environment.sshutil import *
from environment.con_oracle import oracle_connect
from datamoving.public_params import *
from datamoving.loop_time import *
from django.db import connection
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'

"""
执行功能,以及相关方法
"""
logg = logging.getLogger('autoops')


def my_print(args, log):
    """
    :param args:日志内容
    :param log: log对象
    :return: None
    """
    logg.info(args)
    content = '%s%s\n' % (log.content, str(args))
    log.content = content
    log.save()


def get_sh_path(rule_id):
    """
    :param rule_id:规则id
    :return: 规则文件存放路径
    """
    path = Regulation.objects.get(id=rule_id).rule_template
    return path


def init_task(task, log):
    """
    执行时任务初始化
    :param task:
    :param log:
    :return:
    """
    task.status = 1
    task.save()
    task.start_time = datetime.now() if not task.run_step else task.start_time
    log.content = '' if task.run_step is None else log.content
    log.save()


def get_rule_source_target(task, log):
    """
    初始化规则，数据源，目标源
    :param task:
    :param log:
    :return: 脚本路径，表名列表，表名字符，源信息，目标信息
    """
    # 获取规则,数据源,目标源
    rule_id, source_id, target_id = task.rule_id, task.source_id, task.target_id
    my_print("当前规则名称为：%s" % get_rule_name(rule_id), log)
    my_print("当前数据源名称为：%s" % get_datasource(source_id)['datasource_name'][0], log)
    my_print("当前目标源名称为：%s" % get_datasource(target_id)['datasource_name'][0], log)
    # 获取规则中所涉及的表
    sh_path = get_sh_path(rule_id)
    tables, table_names = get_table_info(rule_id)  # 主,从,从,
    # 将数据源信息解密取出
    source = pass_decode(source_id)
    target = pass_decode(target_id)
    return sh_path, tables, table_names, source, target


def check_connecting(source, target, task, log):
    """
    检测数据源连通性
    :param source:
    :param target:
    :param task:
    :param log:
    :return: 机器连接，源，目标oracle连接
    """
    conn_curs, curs = oracle_connect(source)
    database_status = {}
    if curs != 'failed':
        database_status['source'] = SUCCESS
        my_print('源库连接成功!', log)
    else:
        database_status['source'] = ERROR
        my_print('ERROR: 源库连接失败!', log)
        task.database_status = json.dumps(database_status)
        task.save()
        raise Exception('源库连接失败')

    t_conn_curs, t_curs = oracle_connect(target)
    if t_curs != 'failed':
        database_status['target'] = SUCCESS
        my_print('目标库连接成功!', log)
    else:
        database_status['target'] = ERROR
        my_print('ERROR: 目标库连接失败!', log)
        task.database_status = json.dumps(database_status)
        task.save()
        raise Exception('目标库连接失败')
    task.database_status = json.dumps(database_status)
    task.save()
    '''根据写死的条件进行查询信息'''
    # 根据查询条件获取主子表的全部数据量

    #my_print('创建linux连接成功', log)
    conn = create_conn(LINUX_IP(), LINUX_USER(), LINUX_PASS())
    if not conn:
        my_print('linux ip 账号或密码错误', log)
        raise Exception('linux ip 账号或密码错误')
    # if datetime.now() >= task.final_time:
    #     my_print('当前时间不符合系统规定执行时间', log)
    #     raise Exception('当前时间不符合系统规定执行时间')
    return conn, conn_curs, curs, t_conn_curs, t_curs



def result_status(args, task, log, global_dict):
    """
    :param args: 报错信息
    :param task: 任务对象
    :param log: 日志对象
    :param global_dict:数据连接信息
    :return: None
    """
    result = {'success': 3,
              '当前时间不符合系统规定执行时间': 3,
              '主表数据查询结果为空': 3,
              # '源库连接失败': 2,
              # '目标库连接失败': 2,
              # '查询数量与迁移数量不一致': 2}
              }
    if args in list(result.keys()):
        task.status = result[args]
        task.end_time = datetime.now()
        task.total_time = task.end_time.timestamp() - task.start_time.timestamp()
        task.save()
        if global_dict:
            global_dict['conn'].close()
            global_dict['curs'].close()
            global_dict['conn_curs'].close()
            global_dict['t_curs'].close()
            global_dict['t_conn_curs'].close()

    else:
        my_print(str('ERROR:') + args, log)
        task.status = 2
        task.end_time = datetime.now()
        task.total_time = task.end_time.timestamp() - task.start_time.timestamp()
        task.save()
        if global_dict:
            global_dict['conn'].close()
            global_dict['curs'].close()
            global_dict['conn_curs'].close()
            global_dict['t_curs'].close()
            global_dict['t_conn_curs'].close()

        raise args


def execute_task(task, man_f=False):
    """
    根据task_id执行数据迁移工作
    :param task_id: 传入任务id
    man_f 是否人为继续任务(待定功能)
    :return:
    """
    log = Log.objects.get(task_id=task.id)
    init_task(task, log)
    my_print('1.初始化迁移任务', log)
    my_print("临时表名为：transfer_"+str(task.rule_id), log)
    sh_path, tables, table_names, source, target = get_rule_source_target(task, log)
    # 获取规则,数据源,目标源
    my_print('2.开始获取规则脚本路径,表名,目标源,数据源信息', log)
    try:
        conn, conn_curs, curs, t_conn_curs, t_curs = check_connecting(source, target, task, log)
    except Exception as e:
        result_status(traceback.format_exc(), task, log, {})
    my_print('3.获取机器连接,源数据库连接,目标数据库连接', log)
    global_dict = {'log': log, 'sh_path': sh_path, 'tables': tables, 'table_names': table_names, 'source': source,
                   'target': target, 'conn': conn, 'conn_curs': conn_curs, 'curs': curs, 't_conn_curs': t_conn_curs,
                   't_curs': t_curs, 'commit_count': task.commit_count, 'total_count': task.total_count, 'task': task}
    try:
        # table_info = select_main_children(**global_dict) if not task.run_step else json.loads(task.estimate_count)
        # if global_dict['total_count'] is None or global_dict['total_count'] == 0:
        #     print('总数量为空，迁移所有数据')
        #     task.total_count = sum(list(table_info.values()))
        #     task.save()
        # my_print('4.获取本次执行各表的数据总量:', log)
        # my_print(table_info, log)
        # task.estimate_count = json.dumps(table_info)
        # task.save()
        my_print('4.开始执行数据迁移任务：', log)
        '''数据源,目标源,commit条数，涉及的表,所有的id,机器的连接'''
        if get_rule_use_csr(task.rule_id):
            # 执行临时表
            execute_dmp_imp(man_f, **global_dict)
            task.sum_commit = task.sum_delete
            task.save()
        else:
            # 执行不用临时表  基本被舍弃
            without_tmp_table(man_f, **global_dict)

        my_print('5.本次迁移任务全部执行成功！', log)
        result_status('success', task, log, global_dict)

    except Exception as e:
        # 需要一个结果集字典
        if str(e) == '当前时间不符合系统规定执行时间':
            result_status('当前时间不符合系统规定执行时间', task, log, global_dict)
        else:
            result_status(traceback.format_exc(), task, log, global_dict)


def get_rule_use_csr(rule_id: object) -> object:
    """
    :param rule_id:规则id
    :return: 是否使用临时表(1:使用,0:未使用)
    """
    return int(Regulation.objects.get(id=rule_id).use_csr)


def copy_timing(first_task):
    """
    定时器根据首个定时任务创建新任务
    :param first_task: 任务信息
    :return: None
    """
    new_task = Task.objects.filter(task_name__icontains=first_task['task_name']).last().task_name
    num = new_task.split('_')[-1]
    if num.isdigit():
        count = int(num) + 1
        new_name = first_task['task_name'].split('_')[0] + "_" + str(count)
    else:
        count = Task.objects.filter(task_name=first_task['task_name']).count()
        new_name = first_task['task_name'] + "_" + str(count)
    one = datetime.strptime(first_task['start_time'], '%Y-%m-%dT%H:%M:%S') if type(
        first_task['start_time']) == str else \
        first_task['start_time']
    two = datetime.strptime(first_task['final_time'], '%Y-%m-%dT%H:%M:%S') if type(
        first_task['final_time']) == str else \
        first_task['final_time']
    interval = (two.timestamp() - one.timestamp()) / 3600
    first_task['task_name'] = new_name
    first_task['start_time'] = datetime.now()
    first_task['final_time'] = first_task['start_time'] + timedelta(hours=interval)
    if 'id' in first_task.keys():
        del first_task['id']
    task = Task.objects.create(**first_task)
    Log.objects.create(task=task)


def get_table_info(rule_id):
    """
    根据规则id查询表名,主表在前,从表在后
    :param rule_id:规则id
    ！查询条件
    ！comiit条数为0
    """
    rule = Regulation.objects.get(id=rule_id)
    table_list = []
    info = json.loads(rule.table_info)
    for i in info:
        table_list.append(i['name'])
        if 'children' in i.keys():
            for ii in i['children']:
                for key, value in ii.items():
                    if key == 'name':
                        table_list.append(ii['name'])
    table_names = ''
    for tab in table_list:
        table_names += tab + ','
    return table_list, table_names[:-1]


def mini_curs(condition, curs):
    """
    :param condition: sql语句
    :param curs: oracle游标
    :return: 返回游标
    """
    # 去掉sql中不必要的分号
    if ';' in condition:
        condition = condition.replace(';', '')
    curs.prepare(condition)
    curs.execute(None)
    return curs


def select_main_children(**global_dict):
    """
    查询主子表数据总量
    :param global_dict:字典包含连接所有信息
    :return: 返回主子表查询数据总量
    """
    conn = global_dict['conn']
    tables = global_dict['tables']
    table_names = global_dict['table_names']
    source = global_dict['source']
    sh_path = global_dict['sh_path']
    curs = global_dict['curs']
    task = global_dict['task']

    # global condition
    # global max_sql
    table_info = {}
    # 查询所有数据
    '''
    # max_id = get_max_values(conn, curs, table_names, source, sh_path)
    # sqls = execute_sh_two(conn, table_names, 'no', source['db_username'], 'no', '0', sh_path, max_id=max_id)
    '''
    if task.task_type and task.rollback_condition:
        sqls = execute_sh(conn, table_names, 'no', source['db_username'], 'no', '0', sh_path,
                          RB_CONDITION=task.rollback_condition)
    else:
        sqls = execute_sh(conn, table_names, 'no', source['db_username'], 'no', '0', sh_path)
    for i in range(sqls.__len__()):
        if tables[i] in sqls[i]:
            curs = mini_curs(sqls[i], curs)
            all_count = curs.fetchall()
            table_info[tables[i]] = all_count[0][0]
    return table_info


# 通过查询语句获取两段不同的字符串
def get_two_sql_type(condition, curs):
    """
    :param condition:查询语句(查询表中的所有字段)
    :param curs: oracle游标对象
    :return: 返回字段名根据","分割
    """
    curs.prepare(condition)
    result = curs.execute(None)
    # str_filed = ''
    params_filed = ''
    for field in result:
        # str_filed += field[0]+','
        params_filed += ":" + field[0] + ','
    return params_filed[:-1]


def reversed_tables(tables):
    """
    :param tables:表名取反(迁移删除数据时使用)
    :return: 字符串反向表名
    """
    new_tables = list(reversed(tables))
    str_table = ''
    for table in new_tables:
        str_table += table + ','
    return str_table[:-1]


# def insert_temp_table(create_sql, commit_count, drop_sql, conn_curs, task, log, curs):
def insert_temp_table(create_sql, total_count, conn_curs, log, curs):
    """
    向临时表中插入数据
    :param create_sql:获取sh脚本中的临时表语句
    :param total_count: 传入提交总条数
    :param drop_sql: 获取删除临时表语句
    :param conn_curs: 游标连接
    :param task: 任务对象
    :param log: 日志对象
    :param curs: 游标
    :return: None
    """
    try:
        for i in create_sql:
            if 'insert' in i and 'insertflag' not in i:
                curs = mini_curs(i, curs)
                conn_curs.commit()
                if curs.rowcount == 0:
                    logg.info('WARNING:主表数据查询结果为空')
                    my_print('WARNING:主表数据查询结果为空', log)
                    # 删除临时表
                    # delete_temp_table(drop_sql, curs, task, log)
                    return "break"
                    # raise Exception("主表数据查询结果为空")
                logg.info('开始向临时表插入数据,当前插入条数%s' % str(total_count))
                my_print('开始向主表临时表插入数据,当前插入条数%s' % str(total_count), log)
    except Exception as e:
        raise e

def insert_subtemp_table(create_subsql, conn_curs, log, curs):
    """向子表临时表插入子表数据"""
    my_print('开始向子表临时表插入数据', log)
    for i in create_subsql:
        if 'insert' in i:
            curs = mini_curs(i, curs)
            conn_curs.commit()
            if curs.rowcount == 0:
                logg.info('WARNING:子表数据查询结果为空')
               # my_print('WARNING:子表数据查询结果为空', log)
            logg.info('开始向子表临时表插入数据')



def create_temp_talbe(create_sql, task, log, curs):
    """
    创建临时表
    :param create_sql:获取创建临时表sql
    :param task:
    :param log:
    :param curs: 游标
    :return:
    """
    # logg.info("创建临时表：%s" % 'no' + str(task.id))
    logg.info("创建临时表：%s" % 'transfer_' + str(task.rule_id))
    # my_print("创建临时表：%s" % 'no' + str(task.id), log)
    for i in create_sql:
        if 'create' in i:
            curs = mini_curs(i, curs)
            if curs.rowcount == 0:
                # my_print('临时表创建成功', log)
                logg.info('临时表创建成功')
            else:
                logg.info('ERROR: 创建临时表失败！')
                # my_print('ERROR: 创建临时表失败！')
                # raise Exception("创建临时表失败！")


def insert_target_db(insert_sql, commit_count, tables, insert_info, select_count, curs, t_curs, t_conn_curs, task, log):
    """
    :param insert_sql: 获取查询语句
    :param commit_count: 提交条数
    :param tables: 列表表名
    :param insert_info: 记录到actual_count字段统计实时插入数量
    :param select_count:记录实时查询量
    :param curs:源oracle游标
    :param t_curs:目标oracle游标
    :param t_conn_curs:目标连接
    :param task:
    :param log:
    :return:
    """
    my_print("开始进行分批导入数据,当前提交笔数%s" % str(commit_count), log)
    for i in range(insert_sql.__len__()):
        p_field = get_two_sql_type("select A.COLUMN_NAME from user_tab_columns A where TABLE_NAME='%s'" % tables[i],
                                   curs)
        if tables[i] in insert_sql[i]:
            curs.prepare(insert_sql[i])
            val = curs.execute(None)
            values = val.fetchall()
            # curs需要关闭
            if values.__len__() == 0:
                if tables[0] == tables[i]:
                    select_count[tables[i]] = 0
                    #my_print("当前表为:%s 查询数量为:%s" % (tables[i], '0'), log)
                    insert_info[tables[i]] = 0
                    #my_print("当前表为:%s 迁移数量为:%s" % (tables[i], '0'), log)
                    return 'break'
                select_count[tables[i]] = 0
                #my_print("当前表为:%s 查询数量为:%s" % (tables[i], '0'), log)
                insert_info[tables[i]] = 0
                #my_print("当前表为:%s 迁移数量为:%s" % (tables[i], '0'), log)
                continue
            else:
                select_count[tables[i]] = curs.rowcount
                #my_print("当前表为:%s 查询数量为:%s" % (tables[i], curs.rowcount), log)
                # 查询总量和迁移总量对比,对比后再进行删除
                sql = "insert into %s values(%s)" % (tables[i], p_field)
                t_curs.prepare(sql)
                t_curs.executemany(None, values)
                insert_info[tables[i]] = t_curs.rowcount
                #my_print("当前表为:%s 迁移数量为:%s" % (tables[i], t_curs.rowcount), log)
    t_conn_curs.commit()
    my_print("目标表数据迁移成功！", log)
    acutal_count = add_acutal_count(insert_info, 'insert', task)
    my_print(acutal_count, log)
    task.actual_count = json.dumps(acutal_count)
    task.sum_commit = sum(acutal_count.values())
    task.save()
    return task.sum_commit


def delete_source_db(delete_sql, select_count, insert_info, delete_info, tables, conn_curs, task, log, curs):
    """
    :param delete_sql:获取删除语句
    :param select_count: 查询量
    :param insert_info: 插入量
    :param delete_info: 删除量
    :param tables: 表名
    :param conn_curs: 源连接
    :param task: 任务对象
    :param log: 日志对象
    :param curs: oracle游标
    :return:
    """
    if select_count == insert_info:
        # 数据删除
        my_print('查询数量和插入数量一致', log)
        my_print("开始删除源数据!", log)
        new_tables = list(reversed(tables))
        for i in range(delete_sql.__len__()):
            if new_tables[i] in delete_sql[i]:
                curs = mini_curs(delete_sql[i], curs)
                delete_info[new_tables[i]] = curs.rowcount
        conn_curs.commit()
        delete_count = add_acutal_count(delete_info, 'delete', task)
        my_print(delete_count, log)
        task.delete_count = json.dumps(delete_count)
        task.sum_delete = sum(delete_count.values())
        #task.actual_count = delete_count
        #task.sum_commit = task.sum_delete
        task.save()
    else:
        my_print("ERROR:查询数量与迁移数量不一致", log)
        raise Exception('查询数量与迁移数量不一致')
    return task.sum_delete


def delete_temp_table(drop_sql, curs, task, log):
    """
    删除临时表    弃用--只删除临时表数据，不删除临时表
    :param drop_sql:获取删除语句
    :param curs: oracle游标
    :param task: 任务
    :param log: 日志
    :return:
    """
    logg.info("开始删除临时表,临时表名为%s" % 'transfer_' + str(task.rule_id))

    # ("开始删除临时表,临时表名为%s" % 'no' + str(task.id), log)
    try:
        curs.execute(drop_sql)
        logg.info('临时表删除成功！')
        # my_print('临时表删除成功！', log)
    except Exception as e:
        logg.info('ERROR: 临时表删除失败！！')
        raise e

def execute_dmp_imp(man_f, **global_dict):
    """
    执行数据迁移方法
    :param man_f: 是否程序出错后人为确认
    :param global_dict: 数据
    :return:
    """
    source = global_dict['source']
    commit_count = global_dict['commit_count']  #每次commit笔数
    table_names = global_dict['table_names']
    tables = global_dict['tables']
    conn = global_dict['conn']
    curs = global_dict['curs']
    t_curs = global_dict['t_curs']
    t_conn_curs = global_dict['t_conn_curs']
    conn_curs = global_dict['conn_curs']
    sh_path = global_dict['sh_path']
    log = global_dict['log']
    task = global_dict['task']

    """
    执行数据导入导出操作
    :param source: 数据源
    :param target: 目标源
    :param commit_count:需要提交的数据
    :param tables: 涉及的表
    :param ids: 主表要迁移的 id
    :param conn: 机器连接
    :return:
    """
    '''num 系统要循环的次数'''
    commit_count = int(commit_count)
    total_count = int(task.total_count)
    """需要做while ture的判断，并且根据条数查询，直到取不到数据，这里要看看之前的取最大值最小值是否可以删掉"""
    final_time = task.final_time
    insert_info = {}
    delete_info = {}
    select_count = {}
    reversed_name = reversed_tables(tables)
    create_subsql = None
    # 判断是否为回滚任务
    if task.task_type == 1 and task.rollback_condition is not None:
        print('回滚')
        create_sql = execute_sh2(conn, table_names, 'transfer_' + str(task.rule_id), source['db_username'],
                                total_count, '1', sh_path, RB_CONDITION=task.rollback_condition, totalcount=total_count,)
    else:
        print('不回滚')
        #需求需要创建的临时表名为transfer_ruleId
        create_sql = execute_sh2(conn, table_names, 'transfer_' + str(task.rule_id), source['db_username'],
                                total_count, '1', sh_path, totalcount=total_count)
        if table_names.split(',').__len__() > 1:
            create_subsql =execute_sh2(conn, table_names, 'transfer_' + str(task.rule_id), source['db_username'],
                                total_count, '8', sh_path, totalcount=total_count, subTemTableName='transfer_sub' + str(task.rule_id))
    #使用actual_count值，一次性向临时表插入所有要迁移的数据量
    insert_sql = execute_sh(conn, table_names, 'transfer_' + str(task.rule_id), source['db_username'], commit_count, '2', sh_path)
    #delete_sql  删除时，每次迁移量（commit_count）迁移完后删除
    delete_sql = execute_sh(conn, reversed_name, 'transfer_' + str(task.rule_id), source['db_username'], commit_count, '3', sh_path)
    #drop_sql 执行清空临时表的操作
    if create_subsql != None:
        drop_sql = execute_sh2(conn, table_names, 'transfer_' + str(task.rule_id), source['db_username'],
                                total_count, '4', sh_path, totalcount=total_count,
                               subTemTableName='transfer_sub' + str(task.rule_id), )
        save_sql = execute_sh2(conn, table_names, 'transfer_' + str(task.rule_id), source['db_username'], commit_count, '5', sh_path,
                          'Y', 'TRANSFER_LOG', get_rule_name(task.rule_id), task.id,
                               subTemTableName='transfer_sub' + str(task.rule_id))
    else:
        drop_sql = execute_sh2(conn, table_names, 'transfer_' + str(task.rule_id), source['db_username'],
                               total_count, '4', sh_path, totalcount=total_count,
                               subTemTableName=None)
        save_sql = execute_sh2(conn, table_names, 'transfer_' + str(task.rule_id), source['db_username'], commit_count,
                               '5', sh_path,
                               'Y', 'TRANSFER_LOG', get_rule_name(task.rule_id), task.id,
                               subTemTableName=None)
    print(drop_sql, 'drop_sql')
    #从临时表获取commit_count的id内容，根据获取的id内容，去源库中查找对应的数据内容
    #在临时表中将已经迁移的数据状态改为1
    update_sql = execute_sh1(conn, table_names,  'transfer_' + str(task.rule_id), source['db_username'], commit_count, '7', sh_path)
    FLAG = 0 if not task.run_step else task.run_step
    count = 1 if not task.step else task.step
    task_status = 0 if not None else 1
    c = 0
    print(FLAG, '失败后的flag值！！！')
    # 这里不知道为什么获取不到FALG的真实数值,因为存在循环中?
    # 记录每次执行的step,出错后可以根据出错位置继续执行
    try:
        while True:
            if not man_f:  #man_f是false  进if
                if datetime.now() >= final_time:
                    my_print('WARNING:当前时间不符合系统规定执行时间', log)
                    raise Exception('当前时间不符合系统规定执行时间')
                my_print("                                   ", log)
                my_print("                                   ", log)
                my_print("####################################", log)
                my_print('########当前数据迁移次数为:%s########' % count, log)
                my_print("####################################", log)
            else:
                break
            if FLAG == 6 or FLAG == 8 or FLAG == 2:
            #if FLAG > 1:
                try:
                    delete_temp_info(drop_sql, curs, conn_curs)
                    insertflag_result = select_temp_insertflag_status('transfer_' + str(task.rule_id), curs, conn_curs)
                    deleteflag_result = select_temp_deleteflag_status('transfer_' + str(task.rule_id), curs, conn_curs)
                    if insertflag_result == '0' and deleteflag_result != '0':
                        print('1111111111111')
                        task_status = 2
                        task_get_next_time(task)
                        FLAG = 6
                    elif insertflag_result != '0' and deleteflag_result != '0' and insertflag_result == deleteflag_result:
                        task.actual_count = None
                        task.save()
                        print('22222222222')
                        task_status = 2
                        task_get_next_time(task)
                        FLAG = 4
                    elif insertflag_result != '0' and deleteflag_result != '0' and insertflag_result != deleteflag_result:
                        print('33333333333333')
                        task_status = 2
                        task_get_next_time(task)
                        FLAG = 6
                    else:
                        FLAG = 0
                except Exception as err:
                    FLAG = 0
            if FLAG < 1:
                # 创建临时表
                try:
                    create_temp_talbe(create_sql, task, log, curs)
                    FLAG = 1
                except Exception as err:
                    print('临时表已存在，不需要创建', err)
                   # delete_temp_info(drop_sql, curs, conn_curs)
            if FLAG < 2:
                # 向临时表插入数据(total_count)
                result = insert_temp_table(create_sql, total_count, conn_curs, log, curs)
                if result == 'break':
                    break
                result_count = select_count_temp('transfer_' + str(task.rule_id), curs, conn_curs)
                if int(total_count) > int(result_count):
                    total_count = int(result_count)
                FLAG = 2
            if FLAG < 3 and create_subsql != None:
                #创建子表临时表, 创建子表临时表的触发器
                try:
                    create_subtemp_table(create_subsql, task, log, curs)
                    FLAG = 3
                except Exception as err:
                    delete_subtemp_info(drop_sql, curs, conn_curs)
            if FLAG < 4 and create_subsql != None:
                #迁移子表数据到子表临时表
                insert_subtemp_table(create_subsql, conn_curs, log, curs)
                FLAG =4
            if FLAG < 5:
                #批量导入目标库
                insert_target_db(insert_sql, commit_count, tables, insert_info, select_count, curs, t_curs,
                                         t_conn_curs, task, log)
                FLAG = 5
            if FLAG < 6:
                #(6)导入目标库轨迹记录，修改主临时表插入成功标志
                execute_save_log_insert(save_sql, curs, count, log, conn_curs)
                #修改主表临时表插入成功的标志：1成功 0失败
                update_temp_status(update_sql, task, curs, conn_curs)
                FLAG = 6
            if FLAG < 7:
                #(7)删除源库
                delete_source_db(delete_sql, select_count, insert_info, delete_info, tables, conn_curs, task, log, curs)
                t_conn_curs.commit()
                FLAG = 7
            if FLAG < 8:
                result_count = select_count_temp('transfer_' + str(task.rule_id), curs, conn_curs)
                print(result_count, 'result_count')
                if task_status == 2 and int(total_count) > int(result_count) and c == 0:
                    total_count = int(result_count)
                    c += 1
                #(8)删 除源库轨迹记录，修改主临时表删除成功标志
                execute_save_log_delete(save_sql, curs, count, log, conn_curs)
                # 修改主表临时表插入成功的标志：1成功 0失败
                update_temp_status_delete(update_sql, task, curs, conn_curs)
                FLAG = 4
            # estimate_count = eval(task.estimate_count)
            # e_list = list(estimate_count.values())
            # if total_count > int(e_list[0]):
            #     total_count = int(e_list[0])
            actual_count = eval(task.actual_count)
            v_list = list(actual_count.values())
            if int(v_list[0]) == int(total_count):
                #删除临时表内的数据
                delete_subtemp_info(drop_sql, curs, conn_curs)
                my_print('迁移数据量和需要迁移的总量一致', log)
                break
            count += 1
            if man_f:
                break
    except Exception as e:
        task.run_step = FLAG
        task.step = count
        task.save()
        raise e


def select_count_temp(temp, curs, conn_curs):
    """查询主表临时表内的count"""
    sql = "select count(*) from %s where insertflag = 0 or deleteflag = 0" % temp
    mini_curs(sql, curs)
    conn_curs.commit()
    limit = []
    for result in curs:
        for i in str(result):
            if '(' in i:
                limit.append(str(result).index(i))
            if "," in i:
                limit.append(str(result).index(i))
        r = str(result)[limit[0] + 1: limit[1]]
    return r

def task_get_next_time(task):
    """执行失败的任务，将该任务的结束时间向后推迟1天的凌晨3点"""
    import time
    yesterday_time = int(time.time()) + 60 * 60 * 24
    format = "%Y-%m-%d"
    format1 = '%Y-%m-%d %H:%M:%S'
    date = time.strftime(format, time.localtime(yesterday_time))
    date = date + ' 03:00:00'
    time_stamp = time.mktime(time.strptime(date, format1))
    time = time.strftime(format1, time.localtime(time_stamp))
    task.final_time = time
    task.save()


def select_temp_insertflag_status(tempable, curs, conn_curs):
    """新任务执行时，判断临时表内是否还有未处理的数据"""
    sql_insert = "SELECT count(*) FROM %s where %s.INSERTFLAG = 0" % (tempable, tempable)
    curs.prepare(sql_insert)
    curs.execute(None)
    conn_curs.commit()
    limit = []
    for result in curs:
        for i in str(result):
            if '(' in i:
                limit.append(str(result).index(i))
            if "," in i:
                limit.append(str(result).index(i))
        r = str(result)[limit[0] + 1: limit[1]]
    return r

def select_temp_deleteflag_status(tempable, curs, conn_curs):
    """"""
    sql_delete = "SELECT count(*) FROM %s where %s.DELETEFLAG = 0" % (tempable, tempable)
    curs.prepare(sql_delete)
    curs.execute(None)
    conn_curs.commit()
    limit = []
    for result in curs:
        for i in str(result):
            if '(' in i:
                limit.append(str(result).index(i))
            if "," in i:
                limit.append(str(result).index(i))
        r = str(result)[limit[0] + 1: limit[1]]
    return r

def create_subtemp_table(create_subsql, task, log, curs):
    """创建子临时表"""
    for i in create_subsql:
        if 'create' in i:
            curs = mini_curs(i, curs)
            if curs.rowcount == 0:
                # my_print('临时表创建成功', log)
                logg.info('子表临时表创建成功')
            else:
                logg.info('ERROR: 创建子表临时表失败！')

def delete_temp_info(drop_sql, curs, conn_curs):
    """如果主表临时表的两个状态都是1，执行删除内容操作"""
    #for i in drop_sql:
    mini_curs(drop_sql[1], curs)
    conn_curs.commit()


def delete_subtemp_info(drop_sql, curs, conn_curs):

    """如果主表临时表的两个状态都是1，执行删除内容操作"""

    for i in drop_sql:
        mini_curs(i, curs)
        conn_curs.commit()


def update_temp_status(update_sql, task, curs, conn_curs):
    """
    修改临时表内已迁移的数据状态
    :param update_sql:
    :return:
    """
    # my_print("创建临时表：%s" % 'no' + str(task.id), log)
    mini_curs(update_sql[0], curs)
    conn_curs.commit()

def update_temp_status_delete(update_sql, task, curs, conn_curs):
    """
    修改临时表内已迁移的数据状态
    :param update_sql:
    :return:
    """
    # my_print("创建临时表：%s" % 'no' + str(task.id), log)
    mini_curs(update_sql[1], curs)
    conn_curs.commit()


def execute_save_log_delete(save_sql, curs, count, log, conn_curs):
    """
    创建序列，日志表，存储每次迁移的数据内容   -删除源库的轨迹记录
    :param save_sql: 获取相关sql语句
    :param curs:
    :param count:
    :param log:
    :param conn_curs:
    :return:
    """
    if count == 1:
        for sql in save_sql:
            if 'create table' in sql:
                try:
                    curs = mini_curs(sql, curs)
                except Exception as e:
                    if '名称已由现有对象使用' in str(e):
                        my_print('日志记录表已存在,无需进行创建!', log)
                        continue
            elif 'sequence' in sql:
                try:
                    curs = mini_curs(sql, curs)
                    print('SEQUENCE创建成功')
                except Exception as e:
                    if '名称已由现有对象使用' in str(e):
                        my_print('SEQUENCE已存在,无需进行创建!', log)
                        continue
            elif 'insert into' in sql and 'delete' in sql:
                curs = mini_curs(sql, curs)
                conn_curs.commit()
    else:
        for sql in save_sql:
            if 'insert into' in sql and 'delete' in sql:
                curs = mini_curs(sql, curs)
                conn_curs.commit()


def execute_save_log_insert(save_sql, curs, count, log, conn_curs):
    """
    创建序列，日志表，存储每次迁移的数据内容  --插入目标库的轨迹记录
    :param save_sql: 获取相关sql语句
    :param curs:
    :param count:
    :param log:
    :param conn_curs:
    :return:
    """
    if count == 1:
        for sql in save_sql:
            if 'create table' in sql:
                try:
                    curs = mini_curs(sql, curs)
                except Exception as e:
                    if '名称已由现有对象使用' in str(e):
                        my_print('日志记录表已存在,无需进行创建!', log)
                        continue
            elif 'sequence' in sql:
                try:
                    curs = mini_curs(sql, curs)
                    print('SEQUENCE创建成功')
                except Exception as e:
                    if '名称已由现有对象使用' in str(e):
                        my_print('SEQUENCE已存在,无需进行创建!', log)
                        continue
            elif 'insert into' in sql and "'insert' from" in sql:
                curs = mini_curs(sql, curs)
                conn_curs.commit()
    else:
        for sql in save_sql:
            if 'insert into' in sql and "'insert' from" in sql:
                curs = mini_curs(sql, curs)
                conn_curs.commit()


def without_tmp_table(man_f, **global_dict):
    """
    不使用临时表进行迁移(wating)
    :param man_f:
    :param global_dict:
    :return:
    """
    source = global_dict['source']
    commit_count = global_dict['commit_count']
    table_names = global_dict['table_names']
    tables = global_dict['tables']
    conn = global_dict['conn']
    task = global_dict['task']
    curs = global_dict['curs']
    t_curs = global_dict['t_curs']
    t_conn_curs = global_dict['t_conn_curs']
    conn_curs = global_dict['conn_curs']
    sh_path = global_dict['sh_path']
    log = global_dict['log']

    """
    执行数据导入导出操作
    :param source: 数据源
    :param target: 目标源
    :param commit_count:需要提交的数据
    :param tables: 涉及的表
    :param ids: 主表要迁移的 id
    :param conn: 机器连接
    :return:
    """
    '''num 系统要循环的次数'''
    commit_count = int(commit_count)
    # total_commit = json.loads(task.estimate_count)[tables[0]]
    """需要做while ture的判断，并且根据条数查询，直到取不到数据，这里要看看之前的取最大值最小值是否可以删掉"""
    final_time = task.final_time
    insert_info = {}
    delete_info = {}
    select_count = {}
    # fenmu = math.ceil(total_commit / commit_count)
    reversed_name = reversed_tables(tables)

    insert_sql = execute_sh(conn, table_names, 'no' + str(task.id), source['db_username'], commit_count, '2', sh_path,
                            'N')
    delete_sql = execute_sh(conn, reversed_name, 'no' + str(task.id), source['db_username'], commit_count, '3', sh_path,
                            'N')
    save_sql = execute_sh(conn, table_names, 'no' + str(task.id), source['db_username'], commit_count, '5', sh_path,
                          'N', 'TRANSFER_LOG', get_rule_name(task.rule_id), task.id)
    '''
    # max_id = get_max_values(conn, curs, table_names, source, sh_path)
    # insert_sql = execute_sh_two(conn, table_names, 'no' + str(task.id), source['db_username'], commit_count, '2',
    #                             sh_path,
    #                             'N', max_id=max_id)
    # delete_sql = execute_sh_two(conn, reversed_name, 'no' + str(task.id), source['db_username'], commit_count, '3',
    #                             sh_path,
    #                             'N', max_id=max_id)
    # save_sql = execute_sh_two(conn, table_names, 'no' + str(task.id), source['db_username'], commit_count, '5', sh_path,
    #                           'N', 'TRANSFER_LOG', get_rule_name(task.rule_id), task.id, max_id=max_id)
    '''
    FLAG = 0 if not task.run_step else task.run_step
    count = 1 if not task.step else task.step

    # 这里不知道为什么获取不到FALG的真实数值,因为存在循环中?

    try:
        while True:
            if not man_f:
                if datetime.now() >= final_time:
                    my_print('WARNING:当前时间不符合系统规定执行时间', log)
                    raise Exception('当前时间不符合系统规定执行时间')
                my_print("                                   ", log)
                my_print("                                   ", log)
                my_print("####################################", log)
                my_print('########当前数据迁移次数为:%s########' % count, log)
                my_print("####################################", log)
            if FLAG < 1:
                # 分批导入
                result = insert_target_db(insert_sql, commit_count, tables, insert_info, select_count, curs, t_curs,
                                          t_conn_curs,
                                          task, log)
                FLAG = 1
                if result == 'break':
                    my_print('主表数据查询结果为空！', log)
                    break
            if FLAG < 2:
                # execute_save_log(save_sql, curs, count, log, conn_curs)
                FLAG = 2
            # 对比后进行数据删除
            if FLAG < 3:
                delete_source_db(delete_sql, select_count, insert_info, delete_info, tables, conn_curs, task, log, curs)
                FLAG = 0
            if man_f:
                break
            count += 1

    except Exception as e:
        task.run_step = FLAG
        task.step = count
        task.save()
        raise e


def add_acutal_count(emp_info, type, task):
    """
    统计actual_count字段的值
    根据实时的执行操作,追加每个表的实际统计值
    如果首次执行,直接使用emp_info的原值即可
    :param emp_info: 首次操作各个表的值
    :return: 返回和的结果
    """
    if type == "delete":
        db_count = task.delete_count
    else:
        db_count = task.actual_count
    if not db_count:
        # 如果值为空
        return emp_info
    else:
        source = json.loads(db_count)
        for key, value in source.items():
            source[key] = source[key] + emp_info[key]
    return source


def delete_child_main(tables, min, max, curs):
    """
    先删子表再删从表
    :param tables:获取所有要操作的表
    :param min: 最小id
    :param max: 最大id
    :return:
    """
    delete_dict = {}
    reverse_tables = tables[::-1]
    for children in reverse_tables[:-1]:
        curs.prepare('delete from %s where log_id between %s and %s' % (children, min, max))
        curs.execute(None)
        delete_dict[children] = curs.rowcount
    curs.prepare("delete from %s where id between %s and %s" % (reverse_tables[-1], min, max))
    curs.execute(None)
    delete_dict[reverse_tables[-1]] = curs.rowcount
    return delete_dict
    # 字典中取值不需要顺序,所以不需要进行排序
    # 删除字典排序
    # delete_dict = sorted(delete_dict, reverse=True)
    # print(delete_dict)


def delete_dmp_file(source, conn, tables):
    """
    删除dump文件(暂未使用)
    :param source:源数据库信息
    :param conn: 链接
    :param tables: 涉及的所有表
    :return:
    """
    dmp_path = source['file_path']
    for table in tables:
        real_file_path = "rm -rf %s%s.dmp;echo $?" % (dmp_path, table)
        result = remote_excu(conn, real_file_path)
        if result == '0':
            print(table, 'dmp文件删除成功！')
            pass
        else:
            print('dump文件删除失败')


# 进行数据导出操作
def execute_imp(conn, target, source, tables):
    """
    执行导入操作(暂未使用)
    根据源数据库和目标库进行数据导入操作
    :param conn: 源地址链接
    :param target: 目标数据库信息
    :param source: 源数据库信息
    :param tables: 要导出的所有的表
    :return: 返回的导入结果,json格式
    """
    imp_info = {}
    for table in tables:
        imp_command = 'source .bash_profile;imp %s/%s@%s:%s/%s file="%s%s.dmp" tables=%s ignore=y' % (
            target['db_username'], target['db_password'], target['ip'], target['port'], target['server_name'],
            source['file_path'], table, table)
        imp_result = readline_execute(conn, imp_command)
        judge_emp_count(imp_result, imp_info, 'imported', table)
    return imp_info


def judge_emp_count(result, info_dict, key, table):
    """
    根据导出日志获取导出的统计量(暂未使用)
    根据导出和导出的关键字判断影响行数并记录
    :param result: 日志输出结果
    :param info_dict: json类型表信息
    :param key: 传入导出或导出的关键字
    :param table: 对应操作的表
    :return:
    """
    if key in 'exported':
        condition = 'rows exported'
    else:
        condition = 'rows imported'
    for line in result:
        if condition in line:
            info = re.search(' +.+ +', line).group().split()
            try:
                info_dict[table] = int(info[4])
            except IndexError as e:
                try:
                    info_dict[table] = int(info[2])
                except ValueError as ee:
                    info_dict[table] = int(info[1])
    # return info_dict


def execute_sh(conn, table_names, tmptablename, dbuser, commitnum,
               type_num, sh_path, if_use="Y", if_recode='N', rule_name='N', task_id='N', RB_CONDITION=''):
    """
    执行规则sh脚本获取相关的sql语句
    :param conn: 机器连接
    :param table_names: 表名
    :param tmptablename: 临时表名 no+str(task.id)   transfer_str(task.rule_id)
    :param dbuser: 数据库用户
    :param commitnum: 提交条数
    :param type_num: 脚本类型
    :param sh_path: 脚本路径
    :param if_use: 是否使用临时表
    :param if_recode: 是否保存迁移轨迹
    :param rule_name: 规则名
    :param task_id: 任务id
    :param RB_CONDITION: 回滚条件
    :return: 返回相关sql
    """
    if if_use:
        command = "sh %s %s %s %s %s %s %s %s %s %s %s" % (
            sh_path, sh_type(type_num), table_names, tmptablename, dbuser, commitnum, if_use,
            if_recode, rule_name, task_id, RB_CONDITION)
    else:
        command = "sh %s %s %s %s %s %s" % (sh_path, sh_type(type_num), table_names, tmptablename, dbuser, commitnum)
    result = readline_execute(conn, command)
    limit = []
    for line in result:
        if '#' in line:
            limit.append(result.index(line))
    sql_list = []
    for sql in result[limit[0] + 1:limit[1]]:
        sql_list.append(sql.strip())
    return sql_list


def execute_sh1(conn, table_names, tmptablename, dbuser, commitnum,
               type_num, sh_path, if_use="Y"):
    """
    执行规则sh脚本获取相关的sql语句
    :param conn: 机器连接
    :param table_names: 表名
    :param tmptablename: 临时表名 no+str(task.id)   transfer_str(task.rule_id)
    :param dbuser: 数据库用户
    :param commitnum: 提交条数
    :param type_num: 脚本类型
    :param sh_path: 脚本路径
    :param if_use: 是否使用临时表
    :param if_recode: 是否保存迁移轨迹
    :param rule_name: 规则名
    :param task_id: 任务id
    :param RB_CONDITION: 回滚条件
    :return: 返回相关sql
    """
    if if_use:
        command = "sh %s %s %s %s %s %s" % (
            sh_path, sh_type(type_num), table_names, tmptablename, dbuser, commitnum)
    else:
        command = "sh %s %s %s %s %s" % (sh_path, sh_type(type_num), tmptablename, dbuser, commitnum)
    result = readline_execute(conn, command)
    sql = []
    for line in result:
        sql.append(line)
    return sql


def execute_sh3(conn, table_names, tmptablename, dbuser, commitnum,
               type_num, sh_path, if_use="Y", subTemTableName=None):
    """
    执行规则sh脚本获取清空临时表的操作   暂时没用到
    :param conn: 机器连接
    :param table_names: 表名
    :param tmptablename: 临时表名 no+str(task.id)   transfer_str(task.rule_id)
    :param dbuser: 数据库用户
    :param commitnum: 提交条数
    :param type_num: 脚本类型
    :param sh_path: 脚本路径
    :param if_use: 是否使用临时表
    :param if_recode: 是否保存迁移轨迹
    :param rule_name: 规则名
    :param task_id: 任务id
    :param RB_CONDITION: 回滚条件
    :return: 返回相关sql
    """
    if if_use:
        command = "sh %s %s %s %s %s %s %s" % (
            sh_path, sh_type(type_num), table_names, dbuser, tmptablename, commitnum, subTemTableName)
    else:
        command = "sh %s %s %s %s %s" % (sh_path, sh_type(type_num), tmptablename, dbuser, commitnum)
    result = readline_execute(conn, command)
    limit = []
    for line in result:
        if '#' in line:
            limit.append(result.index(line))
    sql_list = []
    for sql in result[limit[0] + 1:limit[1]]:
        sql_list.append(sql.strip())
    return sql_list




def execute_sh2(conn, table_names, tmptablename, dbuser, commitnum,
                type_num, sh_path, if_use="Y", if_recode='N', rule_name='N', task_id='N', RB_CONDITION='None', totalcount=0,
                subTemTableName=' '):
    """
    执行规则sh脚本获取相关的sql语句
    :param conn: 机器连接
    :param table_names: 表名
    :param tmptablename: 临时表名 no+str(task.id)   transfer_str(task.rule_id)
    :param dbuser: 数据库用户
    :param commitnum: 提交条数
    :param type_num: 脚本类型
    :param sh_path: 脚本路径
    :param if_use: 是否使用临时表
    :param if_recode: 是否保存迁移轨迹
    :param rule_name: 规则名
    :param task_id: 任务id
    :param RB_CONDITION: 回滚条件
    :return: 返回相关sql
    """
    if if_use:
        command = "sh %s %s %s %s %s %s %s %s %s %s %s %s %s" % (
            sh_path, sh_type(type_num), table_names, tmptablename, dbuser, commitnum, if_use,
            if_recode, rule_name, task_id, RB_CONDITION, totalcount, subTemTableName)
    else:
        command = "sh %s %s %s %s %s %s" % (sh_path, sh_type(type_num), table_names, tmptablename, dbuser, commitnum)
    result = readline_execute(conn, command)
    limit = []
    for line in result:
        if '#' in line:
            limit.append(result.index(line))
    sql_list = []
    for sql in result[limit[0] + 1:limit[1]]:
        sql_list.append(sql.strip())
    return sql_list



def execute_sh_two(conn, table_names, tmptablename, dbuser, commitnum,
                   type_num, sh_path, if_use="Y", if_recode='N', rule_name='N', task_id='N', max_id='', min_id=''):
    """
    暂时使用(wating for crs_template)
    :param conn:
    :param table_names:
    :param tmptablename:
    :param dbuser:
    :param commitnum:
    :param type_num:
    :param sh_path:
    :param if_use:
    :param if_recode:
    :param rule_name:
    :param task_id:
    :param max_id:
    :param min_id:
    :return:
    """
    if if_use:
        command = "sh %s %s %s %s %s %s %s %s %s %s %s %s" % (
            sh_path, sh_type(type_num), table_names, tmptablename, dbuser, commitnum, if_use,
            if_recode, rule_name, task_id, max_id, min_id)
    else:
        command = "sh %s %s %s %s %s %s" % (sh_path, sh_type(type_num), table_names, tmptablename, dbuser, commitnum)

    result = readline_execute(conn, command)
    limit = []
    for line in result:
        if '#' in line:
            limit.append(result.index(line))
    sql_list = []
    for sql in result[limit[0] + 1:limit[1]]:
        sql_list.append(sql.strip())
    return sql_list


def sh_type(key_work):
    """
    根据现有的脚本参数类型传入关键字获取对应sql语句
    :param key_work:
    :return:
    """
    # type_dict = TYPE_DICT
    for key, value in TYPE_DICT.items():
        if key == key_work:
            return value


def time_to_create_execute(task_dict):
    """
    根据任务决定该任务是否需要定时执行
    :param task_dict:
    :return:
    """
    # 普通创建
    task_dict['status'] = 0
    task_dict['time_rule'] = json.dumps(task_dict['time_rule'])
    if 'rollback_condition' in task_dict.keys():
        if task_dict['rollback_condition']:
            task_dict['rollback_condition'] = json.dumps(task_dict['rollback_condition'])
    task = Task.objects.create(**task_dict)
    Log.objects.create(content='', task=task)
    if int(task_dict['run_way']) == 1:
        add = cron_time(create_execute, task_dict, task.id, task_dict['time_rule'], task_dict['start_time'])


def create_execute(first_task):
    """
    根据任务参数创建任务并执行
    :param first_task:
    :return:
    """
    django.db.close_old_connections()
    new_task = Task.objects.filter(task_name__icontains=first_task['task_name']).last().task_name
    num = new_task.split('_')[-1]
    if num.isdigit():
        count = int(num) + 1
        new_name = first_task['task_name'].split('_')[0] + "_" + str(count)
    else:
        count = Task.objects.filter(task_name=first_task['task_name']).count()
        new_name = first_task['task_name'] + "_" + str(count)
    one = datetime.strptime(first_task['start_time'], '%Y-%m-%dT%H:%M:%S') if type(
        first_task['start_time']) == str else \
        first_task['start_time']
    two = datetime.strptime(first_task['final_time'], '%Y-%m-%dT%H:%M:%S') if type(
        first_task['final_time']) == str else \
        first_task['final_time']
    # 计算下次任务执行时的时间间隔
    interval = (two.timestamp() - one.timestamp()) / 3600
    first_task['task_name'] = new_name
    first_task['start_time'] = datetime.now()
    first_task['final_time'] = first_task['start_time'] + timedelta(hours=interval)
    if 'id' in first_task.keys():
        del first_task['id']
    task = Task.objects.create(**first_task)
    Log.objects.create(task=task)

    execute_task(Task.objects.get(id=task.id))


def get_max_values(conn, curs, table_names, source, sh_path):
    # 获取最大值(暂未使用)
    max_min = execute_sh(conn, table_names, 'no', source['db_username'], '0', '6', sh_path, 'N', )
    for m in max_min:
        if 'max' in m:
            curs = mini_curs(m, curs)
            return curs.fetchall()[0][0]


def userlogin(func):
    """登录验证装饰器"""

    def logincheck(request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponse("无法访问!")
        return func(request, *args, **kwargs)

    return logincheck


# md5校验
def file_md5(filename):
    """
    md5校验值获取文件md5信息
    :param filename:
    :return:
    """
    _FILE_SLIM = (100 * 1024 * 1024)
    calltimes = 0
    hmd5 = hashlib.md5()
    fp = open(filename, "rb")
    # 字节
    f_size = os.stat(filename).st_size
    if f_size > _FILE_SLIM:
        while f_size > _FILE_SLIM:
            hmd5.update(fp.read(_FILE_SLIM))
            f_size /= _FILE_SLIM
            calltimes += 1  # delete
        if (f_size > 0) and (f_size <= _FILE_SLIM):
            hmd5.update(fp.read())
    else:
        hmd5.update(fp.read())
    # 65e18464617c7b457ea37758709895a1
    return (hmd5.hexdigest(), calltimes)


if __name__ == '__main__':
    # result = {'success': 3,
    #           '当前时间不符合系统规定执行时间': 3,
    #           '主表数据查询结果为空': 3}
    # a = '当前时间不符合系统规定执行时间'
    # if a in list(result.keys()):
    #     print(a)
    pass



import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transfer.settings")
django.setup()
import re
import json
import cx_Oracle
from environment.models import *
from datetime import datetime
from environment.sshutil import *
from subprocess import PIPE, Popen
import logging
logg = logging.getLogger('autoops')

# 查询数据并导入
def insert_by_select(conn, curs, filter_dict):
    source = filter_dict['source']
    target = filter_dict['target']
    file = filter_dict['file']
    symbol = filter_dict['symbol']
    count = filter_dict['count']
    sql_select = 'select count(*) from %s where %s %s %s' % (
        source, file, symbol, count)
    result = curs.execute(sql_select)
    select_count = result.fetchall()[0][0]
    print(sql_select)
    print("当前表为%s,数据量:" % source, select_count)
    sql_insert = 'insert into %s select * from %s where %s %s %s' % \
                 (target, source, file, symbol, count)
    print(sql_insert)
    curs.execute(sql_insert)
    insert_count = curs.rowcount
    print("目标表为%s,数据量:" % target, select_count)
    conn.commit()
    if select_count == insert_count:
        return 'success'
    else:
        return 'failed'


# 删除原数据
def delete_source(conn, curs, info):
    # condition = {'table': '"LOG"', "file": '"id"', "symbol": ">", "count": 50}
    delete_sql = 'delete from %s where %s %s %s ' % (info['source'], info['file'], info['symbol'], info['count'])
    print(delete_sql)
    curs.execute(delete_sql)
    print("源数据表为%s数据清理成功!" % info['source'])
    print('清理条数为：%s', curs.rowcount)
    conn.commit()


# 插入数据到oracle
def insert_oracle(conn, curs, table):
    '''oracle数据库'''
    # 数据库名大写可以直接查询，否则遇到小写需要加上双引号
    start = datetime.now()
    sql = 'insert into "%s" values(:1,:2,:3)' % table
    print(sql)
    for i in range(1, 100):
        sql = curs.execute(sql, [i, i, i])
        conn.commit()
    end = datetime.now()
    print(end - start, '耗时')


# 连接oracle
def oracle_connect(info):
    '''oracle 连接'''
    db_info = '%s/%s@%s:%s/%s' % (info['db_username'],
                                                 info['db_password'],
                                                 info['ip'],
                                                 info['port'],
                                                 info['server_name'])
    try:
        conn = cx_Oracle.connect(db_info)  # 连接数据库
        # 当连接对象被破坏或关闭时，任何未完成的更改都将回滚。
        # conn.__enter__()
        curs = conn.cursor()
        return conn, curs

    except Exception as exc:

        error, = exc.args
        print(error)
        #print("Oracle-Error-Code:", error.code)
        #print("Oracle-Error-Message:", error.message)
        logg.info("Oracle-Error-Code:" + str(error.code))
        logg.info("Oracle-Error-Message:" + str(error.message))

        return 'error', 'failed'





# 数据库反向映射
def inspect():
    '''反向生成数据库模型'''
    manage = __file__[:__file__[:__file__.rfind('/')].rfind('/')] + '/manage.py'
    print(manage)
    command = '%s %s inspectdb' % ('python64', manage)
    print(command)
    status = Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell=True)
    status.wait()
    for i in status.stderr.readlines():
        print(bytes.decode(i))
    for line in status.stdout.readlines():
        if b'ForeignKey' in line:
            pass
        '''表名'''
        if b'models.Model' in line:
            table_name = bytes.decode(re.search(b' .+\(', line).group()[1:-1].strip()).upper()
            print(table_name)
        '''字段'''
        if b" = m" in line:
            column = bytes.decode(line[:line.find(b'=')].strip())
            if b'primary_key' in line:
                key = column
                print(key)
            else:
                file = column
                print(file)


# 统计数量
def count_info(conn, curs, table):
    count_sql = 'SELECT count(*) FROM %s' % table
    result = curs.execute(count_sql)
    count = result.fetchall()[0]
    return count[0]


# 根据用户展示数据下的表
def show_tables(conn, curs, user_name):
    tables_sql = "select TABLE_NAME from all_tables where owner=:1"
    print(tables_sql)
    result = curs.execute(tables_sql, [user_name])
    tables = [table[0] for table in result.fetchall()]
    return tables


# 根据所选数据库查询表中相关字段
def show_files_by_tables(conn, curs, table):
    # 查询表名
    select_sql = "SELECT * FROM %s" % table
    curs.execute(select_sql)
    files = [i[0] for i in curs.description]
    return files


# 通过业务名称查询该业务下的机器信息以及oracle配置
def get_config_by_scene(scene_name):
    pass
    # '''通过业务查询机器'''
    # scene = Scene.objects.filter(name=scene_name)
    # print(scene)
    # hosts = Host.objects.filter(scene=scene)
    # print(hosts)
    # info_dict = {}
    # for host in hosts:
    #     if host.username == 'root':
    #         info_dict['username'] = host.username
    #         info_dict['password'] = host.password
    #         info_dict['host'] = host.host
    #         info_dict['port'] = host.port
    #         app = App.objects.filter(host=host).values('values')[0]
    #         info_dict['info_order'] = json.loads(app['values'])['process']
    #         info_dict['server_name'] = json.loads(app['values'])['server_name']
    # return info_dict


# 获取当前连接中的所有表
def select_users(conn, curs):
    sql = "select username from dba_users"
    result = curs.execute(sql)
    info = [user[0] for user in result.fetchall()]
    return info


def oracle_produce(conn, curs):
    procedure = ""
    result = curs.execute(procedure)


def test_sql(file_name, declare_param=''):
    # 替换文件
    conn = create_conn('192.168.43.224', 'oracle', 'oracle')
    remote_upload(conn, '../produce_files/%s.sql' % file_name, '/home/oracle/%s.sql' % file_name)
    command = 'source .bash_profile;sqlplus HTUNDERWRITE/123456@192.168.43.224:1521/ORCL @/home/oracle/%s.sql' % file_name
    result = remote_excu(conn, command)
    # print(result)
    if 'ERROR' in result:
        if 'ORA-00001: unique constraint' in result:
            print('执行失败！,请查看相关日志！')
            print(result)

    else:
        # 执行成功，删除远程文件和本地文件
        print(result)
        # os.remove('../produce_files/%s.sql' % file_name)
        # remote_excu(conn, 'rm -rf /home/oracle/%s.sql' % file_name)
        pass

    if declare_param != '':
        val = re.search(declare_param+':.+', result)
        if val:
            return val.group()




def read_file(k, value):
    rule = 'rule_one'
    f = open('../script_files/%s/%s.sql' %(rule, k[0:6]), 'r', encoding='utf-8')
    list_content = []
    for line in f.readlines():
        if '--$' in line:
            list_content.append(line)
        else:
            for key, val in value.items():
                if key in line:
                    line = line.replace(key, val)
                else:
                    pass
            list_content.append(line)
    f.close()
    f = open('../produce_files/%s.sql' % k, 'w', encoding='utf-8')
    f.writelines(list_content)
    f.close()


def run_moving(all):
    declare_param = ''
    real_value = ''
    for key, value in all[0].items():
        declare_param = value['$2$']
        read_file(key, value)
        real_value = test_sql(key, declare_param)
    real_value = real_value.replace(declare_param+':', '')

    for i in all[1:]:
        for key, value in i.items():
            for k, v in value.items():
                if v == declare_param and 'select' not in key:
                    value[k] = real_value
            read_file(key, value)
            test_sql(key)


def get_host_app(ip, name):
    host = Host.objects.filter(host=ip, name=name)
    print(list(host.values()))
    app = App.objects.filter(host=host)
    print(list(app.values()))

if __name__ == '__main__':

    pass


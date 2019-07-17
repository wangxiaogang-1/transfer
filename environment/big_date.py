# from environment.tests import *
import time
import paramiko
import cx_Oracle
import threading


def select_max(table_name, source_db):
    '''建立首个数据源连接'''
    s_conn, scurs = oracle_connect(source_db['username'],
                                   source_db['password'],
                                   source_db['ip'],
                                   source_db['port'],
                                   source_db['server_name'])
    '''建立其他数据源连接'''
    result = scurs.execute('select max(id) from %s' % table_name)
    max_date = result.fetchone()[0]
    scurs.close()
    s_conn.close()
    return max_date


def delete_source(table, source_db, ids, max_date):
    s_conn, scurs = oracle_connect(source_db['username'],
                                   source_db['password'],
                                   source_db['ip'],
                                   source_db['port'],
                                   source_db['server_name'])
    '''建立其他数据源连接'''
    delete_command = 'delete from %s where %s <= %s' % (table, ids, max_date )
    scurs.execute(delete_command)
    s_conn.commit()
    scurs.close()
    s_conn.close()


def execute_dump(tables, ids, max_date, linux_info, source_db, target_db):
    conn = create_conn(linux_info['ip'], linux_info['username'], linux_info['password'])

    for i in range(tables.__len__()):
        command1_exp = 'source .bash_profile;exp %s/%s@%s:%s/%s file="%s%s.dmp" tables=%s query = \\"where %s \<= "%s"\\"' % (
            source_db['username'],
            source_db['password'],
            source_db['ip'],
            source_db['port'],
            source_db['server_name'],
            source_db['path'],
            tables[i],
            tables[i],
            ids[i],
            max_date)
        print(command1_exp)
        command1_imp = 'source .bash_profile;imp %s/%s@%s:%s/%s file="%s%s.dmp" tables=%s ignore=y' % (
            target_db['username'],
            target_db['password'],
            target_db['ip'],
            target_db['port'],
            target_db['server_name'],
            target_db['path'],
            tables[i], tables[i])
        '生成dmp文件'
        #result1 = remote_excu(conn, command1_exp)
        '删除原表数据'
        # delete_source(tables[i], source_db, ids[i], max_date)
        '导入dmp文件'
        #result2 = remote_excu(conn, command1_imp)
        '删除dmp文件'
        # remove_dump_file(target_db['path'], tables[i], conn)
    conn.close()


def remove_dump_file(path, table_name, conn):
    remote_excu(conn, 'rm -rf %s%s.dmp' % (path, table_name))


def oracle_connect(username, password, ip, port, service_name):
    '''oracle 连接'''
    conn = cx_Oracle.connect('%s/%s@%s:%s/%s' % (username, password, ip, port, service_name))  # 连接数据库
    curs = conn.cursor()
    return conn, curs


def create_conn(host, user, passwd, port=22):
    s = paramiko.SSHClient()  #
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 允许连接不在know_hosts文件中的主机。
    s.connect(hostname=host, port=port, username=user, password=passwd)
    return s


def remote_excu(conn, command):
    # stdin, stdout, stderr = conn.exec_command("source /etc/profile;source ~/.bashrc;"+command)
    stdin, stdout, stderr = conn.exec_command(command)
    stdin.write("Y")  # 一般来说，第一个连接，需要一个简单的交互
    result01 = stderr.read()
    result02 = stdout.read()
    try:
        result1 = result01.decode('gbk')
        result2 = result02.decode('gbk')
    except UnicodeDecodeError:
        result1 = result01.decode()
        result2 = result02.decode()

    if not result1:
        return result2.strip()
    return result1.strip()


if __name__ == '__main__':
    # 第一种情况dmp文件导入导出
    '''机器信息，ip，oracle用户名，oracle密码'''
    linux_info = {"ip": "192.168.43.225", "username": "oracle", "password": "oracle"}
    '''源数据库用户，密码，数据库所在ip，端口，服务名，导出dmp文件存放路径'''
    source_db = {"username": "HTUNDERWRITE", "ip": "192.168.43.225", "password": "123456", "port": "1521",
                 "server_name": "ORCL", "path": "/home/oracle/dump/"}
    '''目标库用户名，密码，数据库所在ip,端口，服务名，导入dmp文件所在路径'''
    target_db = {"username": "HTUNDERWRITE", "ip": "192.168.43.80", "password": "123456", "port": "1521",
                 "server_name": "ORCL", "path": "/home/oracle/dump/"}
    '''导出表按先后顺序排列，主表在前，从表在后'''
    # 该程序默认按照主表中最大的id进行迁移，小于最大id的所有数据都会被迁移
    # table_all = [
    #     'HTIC_QUOTE_PROCESSING_LOG',
    #     'HTIC_QUOTE_PROCESSING_LOG_RULE',
    #     'HTIC_QUOTE_PROCESSING_RESULT']
    # id_all = ['id', 'log_id', 'log_id']
    table_all = [
        'HUATAI_UW_PROCESSING_LOG',
        'HUATAI_UW_PROCESSING_LOG_RULE',
        'HUATAI_UW_PROCESSING_RESULT']
    id_all = ['id', 'uw_id', 'log_id']
    start_time = time.time()

    execute_dump(table_all,
                 id_all,
                 select_max(table_all[0], source_db),
                 linux_info,
                 source_db,
                 target_db)

    end_time = time.time()

    print("耗时：", end_time - start_time)

    pass

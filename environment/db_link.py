import time
import cx_Oracle


# 使用dblink进行数据库连接，首先需要创建dblink


def oracle_connect(username, password, ip, port, service_name):
    '''oracle 连接'''
    conn = cx_Oracle.connect('%s/%s@%s:%s/%s' % (username, password, ip, port, service_name))  # 连接数据库
    curs = conn.cursor()
    return conn, curs


def create_update_link(conn, curs, target_db):
    curs.execute('select DB_LINK from ALL_DB_LINKS')

    command = "CREATE PUBLIC DATABASE LINK AA_LINK CONNECT TO %s " \
              "IDENTIFIED BY %s USING '(DESCRIPTION = (ADDRESS = (PROTOCOL = TCP)" \
              " (HOST = %s)(PORT = %s)) (CONNECT_DATA = (SERVER = DEDICATED) (SERVICE_NAME = %s)))'" % (
    target_db['username'], '"' + target_db['password'] + '"', target_db['ip'], target_db['port'], target_db['server_name'])
    try:

        curs.execute(command)
    except cx_Oracle.DatabaseError as e:
        if e == 'ORA-02011: duplicate database link name':
            pass

    return "AA_LINK"


def moving_data(conn, curs, dblink_name):
    f = open('../script_files/db_link/link.sql')
    content = f.read()
    curs.execute(content)
    curs.execute('DROP PUBLIC DATABASE LINK %s' % dblink_name)
    conn.commit()
    curs.close()
    conn.close()


if __name__ == '__main__':
    start_time = time.time()
    source_db = {"username": "HTUNDERWRITE", "ip": "192.168.43.224", "password": "123456", "port": "1521",
                 "server_name": "ORCL", "path": "/home/oracle/dump/"}
    conn, curs = oracle_connect(source_db['username'], source_db['password'], source_db['ip'], source_db['port'],
                                source_db['server_name'])
    target_db = {"username": "HTUNDERWRITE", "ip": "192.168.43.80", "password": "123456", "port": "1521",
                 "server_name": "ORCL", "path": "/home/oracle/dump/"}
    '创建dblink'
    dblink_name = create_update_link(conn, curs, target_db)
    '执行迁移sql,删除dblink'
    moving_data(conn, curs, dblink_name)
    end_time = time.time()

    print('耗时：', end_time-start_time)
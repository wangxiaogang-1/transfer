
from config.models import *

def get_sys_config(key):
    value = Config.objects.get(key__icontains=key).value
    return value


SUCCESS =  get_sys_config('success')
ERROR = get_sys_config('ERROR')
EXIST = get_sys_config('EXIST')
TYPE_DICT = {
    '0': 'staticsql', '1': 'tmpsql', '2': 'exportsql', '3': 'deletesql', '4': 'dropsql',
    '5': 'savelog', '6': 'getmax', '7': 'updatetmpsql', '8': 'subtmpsql'}

def LINUX_IP():
    return get_sys_config('LINUX_IP')
def LINUX_USER():
    return get_sys_config('LINUX_USER')
def LINUX_PASS():
    return get_sys_config('LINUX_PASS')
# 提出
def PUBLIC_DIR():
    return get_sys_config('PUBLIC_DIR')
# PUBLIC_DIR = 'C:/Users/Leon/Desktop/PUBLIC/'
DATA_SOURCE = {"datasource_name":"数据源名称","ip":"数据源地址","username":"机器用户名","password":"机器密码","port":"数据库端口","db_username":"数据库用户名","db_password":"数据库密码","server_name":"服务名称"}


# if __name__ == '__main__':
#     val = {"0":"staticsql","1":"tmpsql","2":"exportsql","3":"deletesql","4":"dropsql","5":"savelog","6":"getmax"}
#     Config.objects.filter(id=9).update(value=val)
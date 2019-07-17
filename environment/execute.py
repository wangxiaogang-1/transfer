from environment.con_oracle import *


def execute_work():
    """
    根据选择work_id判断所选业务以及业务下的机器
    :return:
    """
    '''获取所选数据库信息'''
    info = get_config_by_scene('数据迁移')
    print(info)
    '''建立连接'''
    # username, password, host, port, server_name
    print('开始建立连接....')
    conn, curs = oracle_connect(info['username'], info['password'], info['host'], info['port'], info['server_name'])
    print('建立连接成功')
    print("连接信息如下", conn)
    count = 0
    for i in info['info_order']:
        i['source'] = translate_name(i['source_table'])
        i['target'] = translate_name(i['target_table'])
        i['file'] = translate_name(i['file'])
        result = insert_by_select(conn, curs, filter_dict=i)
        if result == 'success':
            count += 1

    if count == info['info_order'].__len__():
        print('开始进行源数据清理操作')
        for i in reversed(info['info_order']):
            delete_source(conn, curs, i)
    '''获取相关配置选项'''
    # 所选表,所选字段,字段条件,影响条数,迁移的表
    # 查询数据
    # 数据条数
    # 插入数据,影响条数
    # 核对数据
    # 核对成功, 删除原表数据


def translate_name(source_element):
    if '.' in source_element:
        ss = source_element.split('.')
        if ss[1].islower():
            source = ss[0] + '.' + '"' + ss[1] + '"'
        else:
            source = source_element
    else:
        if source_element.islower():
            source = '"' + source_element + '"'
        else:
            source = source_element
    return source


if __name__ == '__main__':
    # execute_work()
    info = get_config_by_scene('oracle_脚本')
    print(info)

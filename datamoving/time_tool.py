from datetime import datetime
from datetime import timedelta


def get_datetimestr(datetime_obj):
    """"""
    return datetime_obj.strftime("%Y-%m-%d %H:%M:%S")


def get_datestr(datetime_obj):
    """"""
    return datetime_obj.strftime("%Y-%m-%d")


def get_timetstr(datetime_obj):
    """"""
    return datetime_obj.strftime("%H:%M:%S")


def get_datetime(**kwargs):
    """
    获取指定时间前的时间
    :param kwargs:
    :return:
    """
    return datetime.now() - timedelta(
        days=kwargs.get('days') or 0,
        hours=kwargs.get('hours') or 0,
        minutes=kwargs.get('minutes') or 0,
        seconds=kwargs.get('seconds') or 0)


def get_later(**kwargs):
    """
    获取指定时间后的时间
    :param kwargs:
    :return:
    """
    return datetime.now() + timedelta(
        days=kwargs.get('days') or 0,
        hours=kwargs.get('hours') or 0,
        minutes=kwargs.get('minutes') or 0,
        seconds=kwargs.get('seconds') or 0)


def cal_datetime(start_time, end_time):
    """
    计算输入起止时间的差值
    :param start_time: 开始时间
    :param end_time: 结束时间
    :return: 时间差字典
    """
    time_diff = (end_time - start_time)
    time_diff_str = str(time_diff)
    if '.' in str(time_diff_str):
        time_diff_str = time_diff_str.split('.')[0]
    if ',' in time_diff_str:
        time_diff_list = time_diff_str.split(', ')[1].split(':')
    else:
        time_diff_list = time_diff_str.split(':')
    result = {
        'days': time_diff.days,
        'hours': int(time_diff_list[0]),
        'minutes': int(time_diff_list[1]),
        'seconds': int(time_diff_list[2]),
    }
    return result


def cal_last_datetime(**kwargs):
    datetime_list = []
    interval = kwargs.get('interval')
    days = kwargs.get('days')
    for num in range(int(days / interval)):
        datetime_list.insert(0, [
            get_datetime(days=interval * (num + 1)), get_datetime(days=interval * num)
        ])
    return datetime_list


if __name__ == '__main__':
    # print(cal_last_datetime(days=30, interval=5))
    # dat = cal_datetime(datetime.now(), datetime.now())
    # print(dat)
    print(datetime.now().strftime('%H:%M:%S'))
    print((datetime.now()-datetime.now()).strftime('%H:%M:%S'))
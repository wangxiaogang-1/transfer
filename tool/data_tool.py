import json


def to_jsons(queryset):
    """
        将django queryset 转化为json字符串
        :param queryset:
        :return: string
    """
    return json.dumps(list(queryset.values()))


def to_json(queryset):
    return json.dumps(list(queryset.values()))


def trans_data(data):
    new = []
    for d in json.loads(data):
        d['fields']['id'] = d['pk']
        new.append(d['fields'])
    return json.dumps(new)


def trans_data_json(data):
    new = []
    for d in json.loads(data):
        d['fields']['id'] = d['pk']
        new.append(d['fields'])
    return new


def queryset_transducer(queryset):
    result_list = []
    for item in queryset:
        items = []
        if isinstance(item, tuple):
            for tup in item:
                items.append(tup)
        elif isinstance(item, dict):
            items = {}
            for key in item:
                items[key] = item[key]
        result_list.append(items)
    return result_list

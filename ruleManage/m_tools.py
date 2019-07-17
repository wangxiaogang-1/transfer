class PageBase(object):
    """分页设置"""
    default_limit = 10  # 默认一页的数量
    max_limit = 100  # 一页最大的数量
    limit_query_param = 'limit'  # 每页的数量
    offset_query_param = 'offset'  # 第几页(1) if is_page else 从第几条开始(0)
    is_page = False

    def __init__(self, query, request_dic):
        """query=Django的Queryset, request_dic=request.GET或data"""
        self.query = query
        self.request_dic = request_dic
        self.limit = 0

    def get_query(self):
        limit = int(self.request_dic.get(self.limit_query_param, 0)) or self.default_limit
        if self.is_page:
            page = int(self.request_dic.get(self.offset_query_param, 0)) or 1
            offset = (page - 1) * limit
        else:
            offset = int(self.request_dic.get(self.offset_query_param, 0)) or 0
        self.limit = limit
        return self.query[offset:offset + limit]

    def pack_data(self, data):
        count = self.query.count()
        return {
            'count': count,
            'results': data,
        }


class SerBase(object):
    """序列化设置"""
    only = []  # 查询列表
    join = []  # 连接查询列表
    fields = []  # 序列化列表

    def __init__(self, query, many=False):
        """query=Django的Queryset或model对象, many=是否为列表"""
        self.query = query or ()
        self.many = many

    def _get_data_dic(self, m):
        m_dic = {}
        for f in self.fields:
            if type(f) in [list, tuple]:
                if len(f) > 1:
                    m_dic[f[0]] = f[1](m)
                else:
                    m_dic[f[0]] = eval('self.get_{}(m)'.format(f[0]))
            else:
                m_dic[f] = eval('m.{}'.format(f))
        return m_dic

    def data(self):
        if self.many:
            lst = []
            for m in self.query:
                lst.append(self._get_data_dic(m))
            return lst
        else:
            return self._get_data_dic(self.query) if self.query else {}


def m_get_attr(request_dic, *args):
    """输入允许的参数, 返回参数字典"""
    attr_dic = {}
    for arg in args:
        if type(arg) in (list, tuple):
            attr = request_dic.get(arg[0])
            if attr:
                attr_dic[arg[1]] = attr
        else:
            attr = request_dic.get(arg)
            if attr:
                attr_dic[arg] = attr
    return attr_dic


# def m_change_attr(attr_dic, key, func=None, value=None):
#     """修改字典值, 不存在则不修改"""
#     attr = attr_dic.get(key)
#     if attr:
#         if func:
#             attr_dic[key] = func(attr)
#         else:
#             attr_dic[key] = value


def m_get_query(model, ser, attr_dic):
    if not ser.only:
        return model.objects.select_related(*ser.join).filter(**attr_dic)
    return model.objects.only(*ser.only).select_related(*ser.join).filter(**attr_dic)

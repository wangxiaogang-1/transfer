from django.conf.urls import url
from authority.views import *

urlpatterns = [
    # url(r'^login$', login, name='login'),
    # url(r'^logout$', auth_logout, name='logout'),
    # url(r'^check_login$', check_login, name='check_login'),
    # url(r'^group/list$', group_all, name='group_all'),
    # url(r'^group/add$', group_init_add, name='group_init_add'),
    # url(r'^group/update$', group_init_update, name='group_init_update'),
    # url(r'^group/save$', save_group, name='save_group'),
    # url(r'^group/remove$', remove_group, name='remove_group'),
    # url(r'^user/list$', list_user, name='list_user'),
    # url(r'^user/add', add_user, name='add_user'),
    # url(r'^user/save$', save_user, name='save_user'),
    # url(r'^user/remove', remove_user, name='remove_user'),
    # url(r'^user/check_pwd', check_pwd, name='check_pwd'),
    # url(r'^user/set_pwd', set_user_pwd, name='set_user_pwd'),
    # leon_add
    url(r'^user/login', login, name='user_login'), # 用户登陆
    url(r'^user/logout', log_out, name='log_out'), # 用户退出

    url(r'^user/add_init', regist_init, name='user_regist_init'),  # 用户注册
    url(r'^user/add', registe, name='user_registe'), # 用户注册
    url(r'^user/list', user_list, name='user_list'), # 用户list
    url(r'^user/delete', user_delete, name='user_delete'),# 用户删除
    url(r'^user/detail', user_detail, name='user_detail'),# 用户详情展示
    url(r'^user/update', user_update, name='user_update'),# 用户信息修改
    url(r'^user/password/check', user_password_check, name='user_password_check'),# 用户密码修改
    url(r'^user/password/update', user_password_update, name='user_password_update'),  # 用户密码修改

    url(r'^group/list', group_list, name='group_list'),   # 用户组list
    url(r'^group/detail', group_detail, name='group_detail'),# 用户组详细信息展示
    url(r'^group/delete', group_delete, name='group_delete'),# 用户组删除
    url(r'^group/add', group_add, name='group_add'),# 用户组添加
    url(r'^group/init', group_add_init, name='group_add_init'),  # 用户组添加
    url(r'^group/update', group_update, name='update'),# 用户组修改



]

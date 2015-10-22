# -*- coding: utf-8 -*-
__author__ = 'songbowen'

from handler.ui.IndexHandler import IndexHandler
from handler.ui.LoginHandler import LoginHandler
from handler.interface.LogoutHandler import LogoutHandler
from handler.ui.SearchHandler import SearchHandler
from handler.interface.AttendanceHandler import AttendanceHandler
from handler.ui.UserinfoHandler import UserinfoHandler
from handler.ui.RegisterHandler import RegisterHandler
from handler.ui.AdminHandler import AdminIndexHandler, UserManagementHandler, AttendanceManagementHandler


url_pattern = [
    (r"/", IndexHandler),
    (r"/register/", RegisterHandler),
    (r"/login/", LoginHandler),
    (r"/logout/", LogoutHandler),
    (r"/search/", SearchHandler),
    (r"/userinfo/", UserinfoHandler),
    (r"/attence/(\w+)/", AttendanceHandler),
    (r"/admin/", AdminIndexHandler),
    (r"/admin/user/(\d+)?", UserManagementHandler),
    (r"/admin/attence/(\d+)?", AttendanceManagementHandler)
]

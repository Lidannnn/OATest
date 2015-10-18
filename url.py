# -*- coding: utf-8 -*-
__author__ = 'songbowen'

from handler.ui.IndexHandler import IndexHandler
from handler.ui.LoginHandler import LoginHandler
from handler.interface.LogoutHandler import LogoutHandler
from handler.ui.SearchHandler import SearchHandler
from handler.interface.AttenceHandler import AttenceHandler
from handler.ui.UserinfoHandler import UserinfoHandler
from handler.ui.RegisterHandler import RegisterHandler
from handler.ui.AdminHandler import AdminIndexHandler, UserManagementHandler, AttenceManagementHandler


url_pattern = [
    (r"/", IndexHandler),
    (r"/register/", RegisterHandler),
    (r"/login/", LoginHandler),
    (r"/logout/", LogoutHandler),
    (r"/search/", SearchHandler),
    (r"/userinfo/", UserinfoHandler),
    (r"/attence/(\w+)/", AttenceHandler),
    (r"/admin/", AdminIndexHandler),
    (r"/admin/user/(\d+)?", UserManagementHandler),
    (r"/admin/attence/(\d+)?", AttenceManagementHandler)
]

# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import tornado.web

from handler.BaseHandler import BaseHandler


class LogoutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        self.clear_cookie("uid")
        self.redirect(self.get_argument("next", "/login/"))

# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import tornado.web

from lib.models import DB_Session


class BaseHandler(tornado.web.RequestHandler):

    def is_admin(self):
        if not self.current_user:
            return False
        else:
            return self.current_user in ["1"]

    def initialize(self):
        self.session = DB_Session()

    def on_finish(self):
        self.session.close()

    def get_current_user(self):
        return self.get_secure_cookie("uid")

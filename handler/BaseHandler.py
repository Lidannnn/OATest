# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import tornado.web
import sqlalchemy.orm.exc

from lib.models import DB_Session
from lib.models import User


class BaseHandler(tornado.web.RequestHandler):

    def is_admin(self):
        """ Check out if current_user is admin

        :return bool: true if current_user is admin
        """
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

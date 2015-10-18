# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import datetime

import tornado.web
import sqlalchemy.orm.exc

from handler.BaseHandler import BaseHandler
from lib.models import User
from lib.models import Attence
from lib.models import ModifyAttence


class SearchHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        tomonth = datetime.datetime.today().strftime("%Y-%m")
        try:
            user = self.session.query(User).filter(
                User.id == self.current_user,
                User.is_present == 1
            ).one()
            self.render("search.html", current_user=user, active_tag="search", the_month=tomonth, results=[])
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("uid %s not found" % self.current_user)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)

    @tornado.web.authenticated
    def post(self, *args, **kwargs):
        search_month = self.get_argument("search-month")

        try:
            user = self.session.query(User).filter(
                User.id == self.current_user,
                User.is_present == 1
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("uid %s not found" % self.current_user)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)

        # 查询search_month下的所有考勤记录
        results = self.session.query(Attence).filter(
            Attence.date.like(search_month + "%"),
            Attence.userid == user.id
        ).order_by(Attence.date)

        self.render("search.html", current_user=user, active_tag="search",
                    the_month=search_month, results=results.all())

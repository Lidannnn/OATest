# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import datetime

import tornado.web
import sqlalchemy.orm.exc

from handler.BaseHandler import BaseHandler
from lib.models import User
from lib.models import Attence


class IndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        # redirect to admin page if current user is admin
        if self.is_admin():
            self.redirect(self.get_argument("next", "/admin/"))

        is_checkin = False
        is_checkout = False
        checkin_time = ""
        checkout_time = ""
        today = datetime.datetime.today().strftime("%Y-%m-%d")
        try:
            user = self.session.query(User).filter(
                User.id == self.current_user,
                User.is_present == 1
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("uid %s not found" % self.current_user)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)

        try:
            # 今天有一条考勤记录，说明已经打过上班卡
            attence = self.session.query(Attence).filter(
                Attence.userid == self.current_user,
                Attence.date == today
            ).one()

            is_checkin = True
            is_checkout = True if attence.logout is not None else False
            checkin_time = attence.login.strftime("%Y-%m-%d %H:%M:%S")
            checkout_time = attence.logout.strftime("%Y-%m-%d %H:%M:%S") if is_checkout else ""

            self.render("index.html", current_user=user, active_tag="index",
                        is_checkin=is_checkin, is_checkout=is_checkout,
                        checkin_time=checkin_time, checkout_time=checkout_time)
        except sqlalchemy.orm.exc.NoResultFound:
            # 今天没有考勤记录，正常显示首页
            self.render("index.html", current_user=user, active_tag="index",
                        is_checkin=is_checkin, is_checkout=is_checkout,
                        checkin_time=checkin_time, checkout_time=checkout_time)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            # 今天有多条考勤记录
            self.finish("multiple attence records found on %s" % today)



# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import datetime

import tornado.web
import sqlalchemy.orm.exc

from handler.BaseHandler import BaseHandler
from lib.models import User
from lib.models import Attendance


class IndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, *args, **kwargs):

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

        if user.is_admin == 1:
            return self.redirect(self.get_argument("next", "/admin/"))

        try:
            # 今天有一条考勤记录，说明已经打过上班卡
            attendance = self.session.query(Attendance).filter(
                Attendance.userid == user.id,
                Attendance.date == today
            ).one()

            is_checkin = True
            is_checkout = True if attendance.check_out is not None else False
            checkin_time = attendance.check_in.strftime("%Y-%m-%d %H:%M:%S")
            checkout_time = attendance.check_out.strftime("%Y-%m-%d %H:%M:%S") if is_checkout else ""

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
            self.finish("multiple attendance records found on %s" % today)



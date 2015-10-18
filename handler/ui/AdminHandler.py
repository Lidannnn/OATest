# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import datetime

import tornado.web
import sqlalchemy.orm.exc

from handler.BaseHandler import BaseHandler
from lib.models import User, Attence, ModifyAttence
from lib.attence_logic import get_late_overtime_hour


class AdminIndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        if not self.is_admin():
            self.send_error(status_code=404)

        try:
            admin = self.session.query(User).filter(
                User.id == self.current_user
            ).one()
            self.render("admin/index.html", current_user=admin, active_tag="index")
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("uid %s not found" % self.current_user)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)


class UserManagementHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, uid, *args, **kwargs):
        if not self.is_admin():
            self.send_error(status_code=404)

        try:
            admin = self.session.query(User).filter(
                User.id == self.current_user
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("uid %s not found" % self.current_user)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)

        if not uid:
            users = self.session.query(User).order_by(User.id).all()
            self.render("admin/user_manage.html", current_user=admin, active_tag="user_manage", users=users)
        else:
            try:
                user = self.session.query(User).filter(
                    User.id == uid
                ).one()
                the_month = datetime.datetime.now().strftime("%Y-%m")
                self.render("admin/user_attence.html", current_user=admin, active_tag="user_manage",
                            late_hour=0, overtime_hour=0,
                            the_month=the_month, user=user, attences=[])
            except sqlalchemy.orm.exc.NoResultFound:
                self.finish("uid %s not found" % self.current_user)
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.finish("multiple uid %s found" % self.current_user)

    @tornado.web.authenticated
    def post(self, uid, *args, **kwargs):
        if not self.is_admin():
            self.send_error(status_code=404)

        month = self.get_argument("search-month")

        try:
            admin = self.session.query(User).filter(
                User.id == self.current_user
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("uid %s not found" % self.current_user)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)

        if not uid:
            self.finish("uid needed")

        try:
            user = self.session.query(User).filter(
                User.id == uid
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("uid %s not found" % self.current_user)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)

        attences = self.session.query(Attence).filter(
            Attence.userid == user.id,
            Attence.date.like("{month}%".format(month=month))
        ).order_by(Attence.date).all()
        late_hour, overtime_hour = get_late_overtime_hour(user.id, month)
        self.render("admin/user_attence.html", current_user=admin, active_tag="user_manage",
                    late_hour=late_hour, overtime_hour=overtime_hour,
                    the_month=month, user=user, attences=attences)

    @tornado.web.authenticated
    def delete(self, uid, *args, **kwargs):
        # dismiss a user
        if not self.is_admin():
            self.send_error(status_code=404)

        if not uid:
            self.finish("uid needed")

        try:
            user = self.session.query(User).filter(
                User.id == uid
            ).one()
            user.is_present = 0
            self.session.commit()
            self.finish("ok")
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("uid %s not found" % self.current_user)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)


class AttenceManagementHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, uid, *args, **kwargs):
        if not self.is_admin():
            self.send_error(status_code=404)

        try:
            admin = self.session.query(User).filter(
                User.id == self.current_user
            ).one()
            if not uid:
                results = self.session.query(User, Attence, ModifyAttence).filter(
                    ModifyAttence.userid == User.id,
                    Attence.userid == User.id,
                    Attence.date == ModifyAttence.date
                ).order_by(ModifyAttence.id.desc())
                self.render("admin/attence_manage.html", current_user=admin, active_tag="attence_manage", results=results)
            else:
                self.finish("to be done")
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("uid %s not found" % self.current_user)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)

    @tornado.web.authenticated
    def post(self, uid, *args, **kwargs):
        if not self.is_admin():
            self.send_error(status_code=404)

        check_date = self.get_argument("check-date")
        action = self.get_argument("action")

        try:
            modify_attence, original_attence = self.session.query(ModifyAttence, Attence).filter(
                ModifyAttence.userid == uid,
                Attence.userid == uid,
                ModifyAttence.date == check_date,
                Attence.date == check_date
            ).one()

            if action == "pass":
                modify_attence.modify_status = "pass"
                original_attence.login = modify_attence.modified_login
                original_attence.logout = modify_attence.modified_logout
                original_attence.info = modify_attence.info
                if modify_attence.status == "morning-off":
                    original_attence.status = u"上半天请假"
                elif modify_attence.status == "afternoon-off":
                    original_attence.status = u"下半天请假"
                elif modify_attence.status == "day-off":
                    original_attence.status = u"全天请假"
                else:
                    original_attence.status = u"正常"
                self.session.commit()
                self.finish("ok")

            if action == "reject":
                modify_attence.modify_status = "reject"
                original_attence.status = u"审核拒绝"
                self.session.commit()
                self.finish("ok")
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("no attence record on %s" % check_date)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple attence records on %s" % check_date)




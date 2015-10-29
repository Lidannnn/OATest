# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import datetime

import tornado.web
import sqlalchemy.orm.exc

from handler.BaseHandler import BaseHandler
from lib.models import User, Attendance, ModifyAttendance, Team
from lib.attendance_logic import get_late_overtime_hour
from lib.attendance_logic import get_history_late_overtime_hour


class AdminIndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        try:
            admin = self.session.query(User).filter(
                User.id == self.current_user,
                User.is_admin == 1
            ).one()
            self.render("admin/index.html", current_user=admin, active_tag="index")
        except sqlalchemy.orm.exc.NoResultFound:
            self.send_error(status_code=404)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)


class UserManagementHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, uid, *args, **kwargs):
        try:
            admin = self.session.query(User).filter(
                User.id == self.current_user,
                User.is_admin == 1
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            self.send_error(status_code=404)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)

        if not uid:
            # 用户管理页面
            teams = self.session.query(Team).order_by(Team.id).all()
            row2dict = lambda rows: {row.name: row.id for row in rows}
            team_dict = row2dict(teams)

            search_team = self.get_argument("search-team", default="")

            if not search_team or search_team not in team_dict:
                users = self.session.query(User).order_by(User.is_present.desc(), User.id).all()
            else:
                users = self.session.query(User).filter(
                    User.team == team_dict[search_team]
                ).order_by(User.is_present.desc(), User.id).all()

            self.render("admin/user_manage.html", current_user=admin, active_tag="user_manage",
                        users=users, teams=teams, current_team=search_team)
        else:
            # 单个用户考勤管理页面
            try:
                user = self.session.query(User).filter(
                    User.id == uid
                ).one()
                the_month = datetime.datetime.now().strftime("%Y-%m")
                late_hour_total, overtime_hour_total = get_history_late_overtime_hour(user.id)
                self.render("admin/user_attence.html", current_user=admin, active_tag="user_manage",
                            late_hour=0, overtime_hour=0,
                            late_hour_total=late_hour_total, overtime_hour_total=overtime_hour_total,
                            the_month=the_month, user=user, attendances=[])
            except sqlalchemy.orm.exc.NoResultFound:
                self.finish("uid %s not found" % self.current_user)
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.finish("multiple uid %s found" % self.current_user)

    @tornado.web.authenticated
    def post(self, uid, *args, **kwargs):
        month = self.get_argument("search-month")

        try:
            admin = self.session.query(User).filter(
                User.id == self.current_user,
                User.is_admin == 1
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            self.send_error(status_code=404)
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

        attendances = self.session.query(Attendance).filter(
            Attendance.userid == user.id,
            Attendance.date.like("{month}%".format(month=month))
        ).order_by(Attendance.date).all()
        late_hour, overtime_hour = get_late_overtime_hour(user.id, month)
        late_hour_total, overtime_hour_total = get_history_late_overtime_hour(user.id)
        self.render("admin/user_attence.html", current_user=admin, active_tag="user_manage",
                    late_hour=late_hour, overtime_hour=overtime_hour,
                    late_hour_total=late_hour_total, overtime_hour_total=overtime_hour_total,
                    the_month=month, user=user, attendances=attendances)

    @tornado.web.authenticated
    def delete(self, uid, *args, **kwargs):
        # dismiss a user
        if not uid:
            self.finish("uid needed")

        try:
            user = self.session.query(User).filter(
                User.id == uid,
                User.is_present == 1
            ).one()
            user.is_present = 0
            self.session.commit()
            self.finish("ok")
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("uid %s not found" % self.current_user)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)


class AttendanceManagementHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, uid, *args, **kwargs):
        try:
            admin = self.session.query(User).filter(
                User.id == self.current_user,
                User.is_admin == 1
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            self.send_error(status_code=404)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)

        if not uid:
            results = self.session.query(User, Attendance, ModifyAttendance).filter(
                Attendance.id == ModifyAttendance.attendance_id,
                User.id == Attendance.userid
            ).order_by(ModifyAttendance.id.desc()).all()
            self.render("admin/attendance_manage.html", current_user=admin, active_tag="attence_manage",
                        results=results)
        else:
            self.finish("to be done")

    @tornado.web.authenticated
    def post(self, maid, *args, **kwargs):
        try:
            admin = self.session.query(User).filter(
                User.id == self.current_user,
                User.is_admin == 1
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            self.send_error(status_code=404)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)

        if not maid:
            self.finish("modify_attendance_id not given!")

        check_date = self.get_argument("check-date")
        action = self.get_argument("action")
        modify_attendance_id = maid

        try:
            modify_attendance, attendance = self.session.query(ModifyAttendance, Attendance).filter(
                ModifyAttendance.id == modify_attendance_id,
                ModifyAttendance.modify_status == 1,
                Attendance.id == ModifyAttendance.attendance_id,
            ).one()

            if action == "pass":
                # 审批通过
                # 需要设置：
                #   modify_attendance.modify_status,
                #   modify_attendance.modify_time,
                #   attendance.check_in,
                #   attendance.check_out,
                #   attendance.attendance_status
                #   attendance.is_maintainable
                modify_attendance.modify_status = 2
                attendance.check_in = modify_attendance.modify_check_in
                attendance.check_out = modify_attendance.modify_check_out
                attendance.is_maintainable = 3
                if modify_attendance.modify_attendance_status == 1:
                    # 其他类型的维护，多半是忘打卡
                    # 更新考勤状态
                    if attendance.check_in > attendance.legal_check_in:
                        if attendance.check_out < attendance.legal_check_out:
                            # 迟到且早退
                            attendance.attendance_status = 8
                        else:
                            # 迟到
                            attendance.attendance_status = 6
                    else:
                        if attendance.check_out < attendance.legal_check_out:
                            # 早退
                            attendance.attendance_status = 7
                        else:
                            # 正常
                            attendance.attendance_status = 2
                elif modify_attendance.modify_attendance_status == 3:
                    # 上半天请假
                    attendance.legal_check_in += datetime.timedelta(hours=5)
                    if attendance.check_in > attendance.legal_check_in:
                        # 请假还迟到，任性！(╰_╯)
                        if attendance.check_out < attendance.legal_check_out:
                            # 迟到且早退
                            attendance.attendance_status = 8
                        else:
                            # 迟到
                            attendance.attendance_status = 6
                    else:
                        if attendance.check_out < attendance.legal_check_out:
                            # 早退
                            attendance.attendance_status = 7
                        else:
                            # 正常，设置为上半天请假
                            attendance.attendance_status = 3
                elif modify_attendance.modify_attendance_status == 4:
                    # 下半天请假
                    attendance.legal_check_out -= datetime.timedelta(hours=4)
                    if attendance.check_in > attendance.legal_check_in:
                        # 请假还迟到，任性！(╰_╯)
                        if attendance.check_out < attendance.legal_check_out:
                            # 迟到且早退
                            attendance.attendance_status = 8
                        else:
                            # 迟到
                            attendance.attendance_status = 6
                    else:
                        if attendance.check_out < attendance.legal_check_out:
                            # 早退
                            attendance.attendance_status = 7
                        else:
                            # 正常，设置为下半天请假
                            attendance.attendance_status = 4
                elif modify_attendance.modify_attendance_status == 5:
                    # 全天请假
                    attendance.attendance_status = 5
                else:
                    pass
                self.session.commit()
                self.finish("ok")

            if action == "reject":
                modify_attendance.modify_status = 3
                attendance.is_maintainable = 2
                self.session.commit()
                self.finish("ok")
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("no attence record on %s" % check_date)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple attence records on %s" % check_date)




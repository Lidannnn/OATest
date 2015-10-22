# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import datetime
import json

import tornado.web
import sqlalchemy.orm.exc

from handler.BaseHandler import BaseHandler
from lib.models import User
from lib.models import Attendance
from lib.models import ModifyAttendance
from lib.attendance_logic import set_attendance_status_on_check_out


class AttendanceHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, operation, *args, **kwargs):
        try:    # 获取当前用户
            user = self.session.query(User).filter(
                User.id == self.current_user,
                User.is_present == 1
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("uid %s not found" % self.current_user)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)

        if operation.lower() == "info":
            # 获取用户提交的异常考勤记录
            # 用在非管理员查看提交记录的浮层
            check_date = self.get_argument("check-date")
            result = {
                "checkin": "",
                "checkout": "",
                "info": "",
                "status": ""    # lock or nothing。lock意味着前端表格提交按钮置灰
            }

            try:    # 获取当天的原始考勤记录
                attendance = self.session.query(Attendance).filter(
                    Attendance.userid == user.id,
                    Attendance.date == check_date
                ).one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.finish("{uid} has no attendance on {date}".format(
                    uid=user.id, date=check_date
                ))
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.finish("{uid} has multiple attendances on {date}".format(
                    uid=user.id, date=check_date
                ))

            try:    # 获取用户提交过的，状态为待审核的维护记录
                modify_attendance = self.session.query(ModifyAttendance).filter(
                    ModifyAttendance.attendance_id == attendance.id,
                    ModifyAttendance.modify_status == 1
                ).one()
                result["checkin"] = modify_attendance.modify_check_in.strftime("%Y-%m-%d %H:%M:%S")
                result["checkout"] = modify_attendance.modify_check_out.strftime("%Y-%m-%d %H:%M:%S")
                result["info"] = attendance.info
                result["status"] = "lock"
            except sqlalchemy.orm.exc.NoResultFound:
                # 没有状态为待审核的维护记录
                # 返回原始考勤信息已待修改
                result["checkin"] = attendance.check_in.strftime("%Y-%m-%d %H:%M:%S")
                result["checkout"] = attendance.check_out.strftime("%Y-%m-%d %H:%M:%S")
                if attendance.is_maintainable == 3:
                    result["info"] = attendance.info
                    result["status"] = "lock"
            except sqlalchemy.orm.exc.MultipleResultsFound:
                # 有多条待审核的记录，这种情况不应该发生！
                self.finish("{uid} has multiple modify_attendances on {date}".format(
                    uid=user.id, date=check_date
                ))

            self.finish(json.dumps(result))

    @tornado.web.authenticated
    def post(self, operation, *args, **kwargs):
        current_time = datetime.datetime.now()
        current_date = current_time.strftime("%Y-%m-%d")

        try:
            # 获取当前用户
            user = self.session.query(User).filter(
                User.id == self.current_user,
                User.is_present == 1
            ).one()
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("uid %s not found" % self.current_user)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)

        if operation.lower() == "checkin":
            # 处理上班打卡逻辑
            legal_check_in = datetime.datetime.strptime(
                "{date} {time}".format(date=current_date, time=user.banci), "%Y-%m-%d %H:%M"
            )
            legal_check_out = legal_check_in + datetime.timedelta(hours=9)
            try:
                # 获取当天的考勤记录，有记录说明当天已经打过上班卡
                self.session.query(Attendance).filter(
                    Attendance.userid == user.id,
                    Attendance.date == current_date
                ).one()
                self.finish(u"当天已经打过上班卡")
            except sqlalchemy.orm.exc.NoResultFound:
                # 当天没有考勤记录，即当天还没有打卡
                attendance = Attendance(
                    userid=self.current_user,
                    check_in=current_time,
                    date=current_date,
                    updatetime=current_time,
                    legal_check_in=legal_check_in,
                    legal_check_out=legal_check_out
                )
                self.session.add(attendance)
                self.session.commit()
                self.finish("ok")
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.finish(u"当天有多条打卡记录，请联系songbowen@qiyi.com")

        elif operation.lower() == "checkout":
            # 处理下班打卡逻辑
            try:
                # 获取当天考勤记录
                attendance = self.session.query(Attendance).filter(
                    Attendance.userid == user.id,
                    Attendance.date == current_date
                ).one()

                attendance.check_out = current_time   # 记录下班时间
                self.session.commit()

                set_attendance_status_on_check_out(self.session, attendance)   # 计算当天考勤状态

                self.finish("ok")
            except sqlalchemy.orm.exc.NoResultFound:
                # 当天还没有考勤记录
                self.finish(u"没有打卡记录，请先打上班卡")
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.finish(u"当天有多条打卡记录，请联系songbowen@qiyi.com")

        elif operation.lower() == "submit_info":
            # 处理用户提交的异常考核申请
            check_date = self.get_argument("check-date")
            check_in_time = self.get_argument("checkin-time")
            check_out_time = self.get_argument("checkout-time")
            info = self.get_argument("info")
            status = self.get_argument("status")

            try:
                # 把checkin_time & checkout_time转换成datetime对象
                check_in_time = datetime.datetime.strptime(check_in_time, "%Y-%m-%d %H:%M:%S") if check_in_time != "" \
                    else datetime.datetime.strptime(check_date, "%Y-%m-%d")
                check_out_time = datetime.datetime.strptime(check_out_time, "%Y-%m-%d %H:%M:%S") if check_out_time != "" \
                    else datetime.datetime.strptime(check_date, "%Y-%m-%d")
            except ValueError:
                self.finish(u"考勤时间格式错误")

            try:
                # 获取check_date的，状态为可以维护的原始打卡记录
                attendance = self.session.query(Attendance).filter(
                    Attendance.userid == user.id,
                    Attendance.date == check_date,
                    Attendance.is_maintainable == 2
                ).one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.finish(u"{check_date}没有需要维护的打卡记录".format(check_date=check_date))
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.finish(u"{check_date}有多条需要维护的打卡记录，请联系songbowen@qiyi.com".format(check_date=check_date))

            try:
                # 获取attendance的待审核记录
                # 有待审核的记录，不可以再提交
                self.session.query(ModifyAttendance).filter(
                    ModifyAttendance.attendance_id == attendance.id,
                    ModifyAttendance.modify_status == 1
                ).one()
                self.finish(u"{check_date}已有待审核的记录，不能在提交".format(check_date=check_date))
            except sqlalchemy.orm.exc.NoResultFound:
                # check_date没有审核中的打卡记录，需要创建一条记录
                modify_attendance = ModifyAttendance(
                    attendance_id=attendance.id,
                    modify_check_in=check_in_time,
                    modify_check_out=check_out_time,
                    modify_status=1,
                    modify_attendance_status=status,
                    modify_info=info
                )
                attendance.info = info
                attendance.is_maintainable = 3
                self.session.add(modify_attendance)
                self.session.commit()
                self.finish("ok")
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.finish(u"{check_date}有多条待审核的打卡记录，请联系songbowen@qiyi.com".format(check_date=check_date))

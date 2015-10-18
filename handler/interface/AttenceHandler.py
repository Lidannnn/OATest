# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import datetime
import json

import tornado.web
import sqlalchemy.orm.exc

from handler.BaseHandler import BaseHandler
from lib.models import User
from lib.models import Attence
from lib.models import ModifyAttence
from lib.attence_logic import set_attence_status


class AttenceHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, operation, *args, **kwargs):
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

        if operation.lower() == "info":
            check_date = self.get_argument("check-date")
            result = {
                "checkin": "",
                "checkout": "",
                "info": "",
                "status": ""    # lock or nothing。lock意味着前端表格提交按钮置灰
            }
            try:
                # modify_attence表中有提交记录
                # 说明用户已经提交过审核申请，需要根据审核状态返回
                # 状态为reject的时候可以再次提交
                modified_attence = self.session.query(ModifyAttence).filter(
                    ModifyAttence.userid == user.id,
                    ModifyAttence.date == check_date
                ).one()

                if modified_attence.modified_login is not None:
                    checkin_time = modified_attence.modified_login.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    checkin_time = ""
                if modified_attence.modified_logout is not None:
                    checkout_time = modified_attence.modified_logout.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    checkout_time = ""

                result["checkin"] = checkin_time
                result["checkout"] = checkout_time
                result["info"] = modified_attence.info
                if modified_attence.modify_status not in ["reject"]:
                    result["status"] = "lock"
            except sqlalchemy.orm.exc.NoResultFound:
                # modify_attence表中没有找到考勤提交记录
                # 需要从attence表中获取原始考勤记录
                try:
                    attence = self.session.query(Attence).filter(
                        Attence.userid == user.id,
                        Attence.date == check_date
                    ).one()

                    if attence.login is not None:
                        checkin_time = attence.login.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        checkin_time = ""
                    if attence.logout is not None:
                        checkout_time = attence.logout.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        checkout_time = ""

                    result["checkin"] = checkin_time
                    result["checkout"] = checkout_time
                except sqlalchemy.orm.exc.NoResultFound:
                    # attence表中没有check_date的考勤记录
                    result["info"] = u"{date}没有考勤记录".format(date=check_date)
                except sqlalchemy.orm.exc.MultipleResultsFound:
                    result["info"] = u"{date}有多条考勤记录，请联系songbowen@qiyi.com".format(date=check_date)
            except sqlalchemy.orm.exc.MultipleResultsFound:
                # modify_attence表中有多条考勤记录
                result["info"] = u"{date}有多条考勤记录，请联系songbowen@qiyi.com".format(date=check_date)
            self.finish(json.dumps(result))

    @tornado.web.authenticated
    def post(self, operation, *args, **kwargs):
        the_time = datetime.datetime.now()
        the_date = the_time.strftime("%Y-%m-%d")

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
            legal_checkin = datetime.datetime.strptime(
                "{date} {time}".format(date=the_date, time=user.banci), "%Y-%m-%d %H:%M"
            )
            legal_checkout = legal_checkin + datetime.timedelta(hours=9)
            try:
                # 获取当天的考勤记录，有记录说明当天已经打过上班卡
                self.session.query(Attence).filter(
                    Attence.userid == user.id,
                    Attence.date == the_date
                ).one()
                self.finish(u"当天已经打过上班卡")
            except sqlalchemy.orm.exc.NoResultFound:
                # 当天没有考勤记录，即当天还没有打卡
                checkin = Attence(
                    userid=self.current_user,
                    login=the_time,
                    date=the_date,
                    updatetime=the_time,
                    legal_checkin=legal_checkin,
                    legal_checkout=legal_checkout
                )
                self.session.add(checkin)
                self.session.commit()
                self.finish("ok")
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.finish(u"当天有多条打卡记录，请联系songbowen@qiyi.com")

        elif operation.lower() == "checkout":
            # 处理下班打卡逻辑
            try:
                # 获取当天考勤记录
                attence = self.session.query(Attence).filter(
                    Attence.userid == user.id,
                    Attence.date == the_date
                ).one()

                attence.logout = the_time   # 记录下班时间

                self.session.commit()
                set_attence_status(user.id, attence.date)   # 计算当天考勤状态

                self.finish("ok")
            except sqlalchemy.orm.exc.NoResultFound:
                # 当天还没有考勤记录
                self.finish(u"没有打卡记录，请先打上班卡")
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.finish(u"当天有多条打卡记录，请联系songbowen@qiyi.com")

        elif operation.lower() == "submit_info":
            # 处理用户提交的异常考核申请
            check_date = self.get_argument("check-date")
            checkin_time = self.get_argument("checkin-time")
            checkout_time = self.get_argument("checkout-time")
            info = self.get_argument("info")
            status = self.get_argument("status")

            try:
                # 把checkin_time & checkout_time转换成datetime对象
                checkin_time = datetime.datetime.strptime(checkin_time, "%Y-%m-%d %H:%M:%S") if checkin_time != "" \
                    else datetime.datetime.strptime(check_date, "%Y-%m-%d")
                checkout_time = datetime.datetime.strptime(checkout_time, "%Y-%m-%d %H:%M:%S") if checkout_time != "" \
                    else datetime.datetime.strptime(check_date, "%Y-%m-%d")
            except ValueError:
                self.finish(u"考勤时间格式错误")

            try:
                # 获取check_date的原始打卡记录
                original_attence = self.session.query(Attence).filter(
                    Attence.userid == user.id,
                    Attence.date == check_date
                ).one()
            except sqlalchemy.orm.exc.NoResultFound:
                self.finish(u"{check_date}没有打卡记录".format(check_date=check_date))
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.finish(u"{check_date}有多条打卡记录，请联系songbowen@qiyi.com".format(check_date=check_date))

            try:
                # 获取check_date的审核记录
                modified_attence = self.session.query(ModifyAttence).filter(
                    ModifyAttence.userid == user.id,
                    ModifyAttence.date == check_date
                ).one()
                # 有记录的时候，检查审核状态
                if modified_attence.modify_status in ["reject"]:
                    # 审核拒绝的申请，可以再次提交
                    modified_attence.modified_login = checkin_time
                    modified_attence.modified_logout = checkout_time
                    modified_attence.info = info
                    modified_attence.status = status
                    modified_attence.modify_status = "todo"
                    original_attence.info = info
                    self.session.commit()
                    self.finish("ok")
                elif modified_attence.modify_status in ["pass", "todo"]:
                    # 审核通过和待处理，不可以重复提交
                    self.finish(u"待处理或者已经通过，不能再次提交")
            except sqlalchemy.orm.exc.NoResultFound:
                # check_date没有审核中的打卡记录，需要创建一条记录
                if original_attence.login is None:
                    # check_date没有上班打卡记录的时候，生成一个
                    original_login = datetime.datetime.strptime(check_date, "%Y-%m-%d")
                else:
                    original_login = original_attence.login

                if original_attence.logout is None:
                    # check_date没有下班打卡记录的时候，生成一个
                    original_logout = datetime.datetime.strptime(check_date, "%Y-%m-%d")
                else:
                    original_logout = original_attence.logout

                modified_attence = ModifyAttence(
                    userid=user.id,
                    date=check_date,
                    original_login=original_login,
                    original_logout=original_logout,
                    status=status,
                    info=info,
                    modified_login=checkin_time,
                    modified_logout=checkout_time
                )
                original_attence.info = info
                self.session.add(modified_attence)
                self.session.commit()
                self.finish("ok")
            except sqlalchemy.orm.exc.MultipleResultsFound:
                self.finish(u"{check_date}有多条打卡记录，请联系songbowen@qiyi.com".format(check_date=check_date))

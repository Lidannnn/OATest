# -*- coding: utf-8 -*-
__author__ = 'songbowen'

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import TIMESTAMP
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship


engine = create_engine("postgresql://postgres:root@localhost/OATest", encoding="utf-8")
Base = declarative_base()
DB_Session = sessionmaker(bind=engine)


class Attence(Base):
    """
    id:                 考勤id
    userid:             用户id
    login:              用户上班打卡时间
    logout:             用户下班打卡时间
    date:               考勤日期
    updatetime:         考勤状态更新时间，用途未知！！！！
    status:             考勤状态 - 正常、迟到、早退、迟到且早退、旷工、周末加班、审核通过、审核拒绝、上半天请假、下半天请假、全天请假
    latecount:          当月迟到次数
    info:               用户的异常考勤备注
    legal_checkin:      规定上班签到时间。增加此列用于防止用户更新上班时间，导致迟到时间计算错误
    legal_checkout:     legal_checkin + 9 hours
    """
    __tablename__ = "attence"

    id = Column(Integer, primary_key=True, nullable=False)
    userid = Column(Integer, ForeignKey("user.id"))
    login = Column(TIMESTAMP)
    logout = Column(TIMESTAMP)
    date = Column(String, nullable=False)
    updatetime = Column(TIMESTAMP, nullable=False)
    status = Column(String)
    latecount = Column(Integer)
    info = Column(String)

    legal_checkin = Column(TIMESTAMP)
    legal_checkout = Column(TIMESTAMP)

    def __repr__(self):
        return "<Attence(userid={userid}, login={login}, logout={logout}, date={date}, updatetime={updatetime})>"\
            .format(userid=self.userid, login=self.login, logout=self.logout, date=self.date, updatetime=self.updatetime)


class ModifyAttence(Base):
    """
    id:                     异常考勤id
    userid:                 用户id
    original_login:         原始上班打卡时间
    original_logout:        原始下班打卡时间
    date:                   打卡日期
    status:                 原始考勤状态
    info:                   用户提交的异常考勤说明
    modify_status:          考勤审核状态 - todo, pass, reject
    modified_login:         维护后的上班打卡时间
    modified_logout:        维护后的下班打卡时间
    """
    __tablename__ = "modify_attence"

    id = Column(Integer, primary_key=True, nullable=False)
    userid = Column(Integer, ForeignKey("user.id"))
    original_login = Column(TIMESTAMP)
    original_logout = Column(TIMESTAMP)
    date = Column(String, nullable=False)
    status = Column(String)
    info = Column(String)
    modify_status = Column(String, default="todo")
    modified_login = Column(TIMESTAMP)
    modified_logout = Column(TIMESTAMP)

    def __repr__(self):
        return "<ModifyAttence(userid={userid}, status={status})>".format(userid=self.userid, status=self.modify_status)


class User(Base):
    """
    id:                 用户id
    email:              用户邮箱
    name:               用户姓名
    passcode:           用户密码
    createdate:         用户注册时间
    banci:              用户上班时间
    latecount:          用户当前的迟到次数
    company:            用户的公司
    team:               用户所在的工作组
    late_hour:          用户当月累计的缺勤时间
    off_hour_taken:     用户使用的调休时间
    off_hour_total:     用户总共的调休时间
    is_present:         用户是否在职。1为在职，0为离职
    """
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    passcode = Column(String, nullable=False)
    createdate = Column(TIMESTAMP, nullable=False)
    banci = Column(String, nullable=False, default="10:00")
    latecount = Column(Integer, default=0)

    company = Column(String, default="")
    team = Column(String, default="")
    late_hour = Column(Integer, default=0, nullable=False)
    off_hour_taken = Column(Integer, default=0, nullable=False)
    off_hour_total = Column(Integer, default=0, nullable=False)
    is_present = Column(Integer, default=1, nullable=False)

    attence = relationship("Attence", backref="user")
    modify_attence = relationship("ModifyAttence", backref="user")

    def __repr__(self):
        return "<User(id={id}, email={email})>".format(id=self.id, email=self.email)


if __name__ == "__main__":
    # Base.metadata.create_all(engine)
    session = DB_Session()
    # print session.query(User).filter(User.email == 'songbowen@qiyi.com').one_or_none()
    results = session.query(Attence, ModifyAttence).filter(
            Attence.date.like("2015-09" + "%"),
            Attence.userid == 37,
            ModifyAttence.userid == 37
        ).order_by(Attence.date)
    print len(results.all())

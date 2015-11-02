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


engine = create_engine("postgresql://postgres:root@localhost:5432/test", encoding="utf-8")
Base = declarative_base()
DB_Session = sessionmaker(bind=engine)


class Company(Base):
    """ public.company

    This table stores all company name
    """
    __tablename__ = "company"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    user = relationship("User", backref="company_name")

    def __repr__(self):
        return "<Company(id={id}, company_name={name})>".format(
            id=self.id, name=self.company_name
        )


class Team(Base):
    """ public.team

    This table stores all team in our company.
    """
    __tablename__ = "team"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    user = relationship("User", backref="team_name")

    def __repr__(self):
        return "<Team(id={id}, team_name={name})>".format(
            id=self.id, name=self.team_name
        )


class AttendanceStatus(Base):
    """ public.attendance_status

    This table stores all status that are used in public.attendance.attendance_status
    """
    __tablename__ = "attendance_status"

    id = Column(Integer, primary_key=True)
    status_name = Column(String, unique=True)

    attendance = relationship("Attendance", backref="status")
    modify_attendance = relationship("ModifyAttendance", backref="attendance_status")

    def __repr__(self):
        return "<AttendanceStatus(id={id}, status={status})>".format(
            id=self.id, status=self.status_name
        )


class MaintainStatus(Base):
    """ public.maintain_status

    This table stores all maintain status that are used in public.attendance.is_maintainable
    """
    __tablename__ = "maintain_status"

    id = Column(Integer, primary_key=True)
    status_name = Column(String, unique=True)

    attendance = relationship("Attendance", backref="maintain_status")

    def __repr__(self):
        return "<MaintainStatus(id={id}, status={status})>".format(
            id=self.id, status=self.status_name
        )


class Attendance(Base):
    """ public.attendance

    This table is meant to record user attendance.
    """
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True)
    userid = Column(Integer, ForeignKey("user.id"))
    check_in = Column(TIMESTAMP)
    check_out = Column(TIMESTAMP)
    date = Column(String, nullable=False)
    updatetime = Column(TIMESTAMP, nullable=False)
    attendance_status = Column(Integer, ForeignKey("attendance_status.id"), default=1)
    latecount = Column(Integer)
    info = Column(String)
    legal_check_in = Column(TIMESTAMP)
    legal_check_out = Column(TIMESTAMP)
    is_maintainable = Column(Integer, ForeignKey("maintain_status.id"), default=1)

    modify_attendance = relationship("ModifyAttendance", backref="attendance")

    def __repr__(self):
        return "<Attence(userid={userid}, login={login}, logout={logout}, date={date})>".format(
            userid=self.userid, login=self.check_in, logout=self.check_out, date=self.date
        )


class ModifyStatus(Base):
    """ public.modify_status

    This table stores all modify status that are used in public.modify_attendance
    """
    __tablename__ = "modify_status"

    id = Column(Integer, primary_key=True)
    status_name = Column(String, unique=True)

    modify_attendance = relationship("ModifyAttendance", backref="status")

    def __repr__(self):
        return "<ModifyStatus(id={id}, status={status})>".format(
            id=self.id, status=self.status_name
        )


class ModifyAttendance(Base):
    """public.modify_attendance

    This table stores all attendance that user submits to modify
    """
    __tablename__ = "modify_attendance"

    id = Column(Integer, primary_key=True)
    attendance_id = Column(Integer, ForeignKey("attendance.id"))
    modify_check_in = Column(TIMESTAMP)
    modify_check_out = Column(TIMESTAMP)
    modify_status = Column(Integer, ForeignKey("modify_status.id"), default=1)
    modify_time = Column(TIMESTAMP)
    modify_attendance_status = Column(Integer, ForeignKey("attendance_status.id"), default=1)
    modify_info = Column(String)

    def __repr__(self):
        return "<ModifyAttence(attendance_id={attendance_id}, modify_time={modify_time})>".format(
            attendance_id=self.attendance_id, modify_time=self.modify_time
        )


class User(Base):
    """public.user

    This table stores all user.
    """
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    passcode = Column(String, nullable=False)
    createdate = Column(TIMESTAMP, nullable=False)
    banci = Column(String, nullable=False, default="10:00")
    latecount = Column(Integer, default=0)
    company = Column(Integer, ForeignKey("company.id"), default=1)
    team = Column(Integer, ForeignKey("team.id"), default=1)
    is_present = Column(Integer, default=1)
    is_admin = Column(Integer, default=0)
    dismiss_time = Column(TIMESTAMP)

    attendance = relationship("Attendance", backref="user")

    def __repr__(self):
        return "<User(id={id}, email={email})>".format(id=self.id, email=self.email)


if __name__ == "__main__":
    # Base.metadata.create_all(engine)
    session = DB_Session()
    companies = session.query(Company).order_by(Company.id).all()

    row2dict = lambda rows: {row.name: row.id for row in rows}
    print row2dict(companies)
    # print map(row2dict, companies)
    # result = session.query(Attendance).all()
    # print result[0].status.status_name
    # results = session.query(User, Attendance, ModifyAttendance).filter(
    #     Attendance.id == ModifyAttendance.attendance_id,
    #     User.id == Attendance.userid
    # ).order_by(ModifyAttendance.id.desc())
    # results = session.query(User).order_by(
    #     User.is_present.desc(), User.id
    # )
    # print results.all()

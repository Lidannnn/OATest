# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import datetime

import sqlalchemy.orm.exc

from lib.models import User, Attendance
from lib.models import DB_Session


def set_legal_check(uid):
    """ Set user's legal checkin & checkout time
    This function should only run for old employees.
    :param uid: user id
    """
    session = DB_Session()
    try:
        user = session.query(User).filter(
            User.id == uid,
            User.is_present == 1
        ).one()
    except sqlalchemy.orm.exc.NoResultFound:
        print "uid %s not found" % uid
        return None
    except sqlalchemy.orm.exc.MultipleResultsFound:
        print "multiple uid %s found" % uid
        return None

    attendances = session.query(Attendance).filter(
        Attendance.userid == user.id
    )
    for attendance in attendances:
        if attendance.legal_check_in is not None:
            print "legal_checkin already set @ %s" % attendance.legal_check_in
        else:
            attendance.legal_check_in = datetime.datetime.strptime(
                "{date} {time}".format(date=attendance.date, time=user.banci),
                "%Y-%m-%d %H:%M"
            )
        attendance.legal_check_out = attendance.legal_check_in + datetime.timedelta(hours=9)

    session.commit()
    session.close()


def get_late_overtime_hour(uid, month):
    """ Get user's late hours in the month

    :param uid: user id
    :param month: format 'yyyy-mm'
    """
    session = DB_Session()
    late_hour_total = 0
    overtime_hour_total = 0
    user = session.query(User).filter(
        User.id == uid
    ).one()
    attendances = session.query(Attendance).filter(
        Attendance.userid == user.id,
        Attendance.date.like("{month}%".format(month=month))
    ).order_by(Attendance.date).all()
    for attendance in attendances:
        if attendance.attendance_status in [1, 11]:
            # 考勤状态待定，先不处理
            continue
        if attendance.attendance_status == 2 and datetime.datetime.strptime(attendance.date, "%Y-%m-%d").weekday() in [5, 6]:
            # 周末，考勤状态正常，不处理
            continue
        if attendance.attendance_status in [2, 3, 4, 6]:
            # 正常下班情况，计算加班时间
            # 正常下班包括：正常、上午请假、下午请假、迟到
            overtime_hour_total += (attendance.check_out - attendance.legal_check_out).seconds / 3600
        if attendance.attendance_status in [3, 4]:
            # 请半天假，缺勤4小时
            late_hour_total += 4
        if attendance.attendance_status in [5, 9]:
            # 全天假和旷工，缺勤8小时
            late_hour_total += 8
        if attendance.attendance_status in [6, 8]:
            # 上班晚，需要计算缺勤时间
            late_hour_total += (attendance.check_in - attendance.legal_check_in).seconds / 3600 + 1
        if attendance.attendance_status in [7, 8]:
            # 下班早，需要计算缺勤时间
            late_hour_total += (attendance.legal_check_out - attendance.legal_check_out).seconds / 3600 + 1
        if attendance.attendance_status in [10]:
            overtime_hour_total += (attendance.check_out - attendance.check_in).seconds / 3600

        # print attendance.date, late_hour_total, overtime_hour_total
    session.close()
    return late_hour_total, overtime_hour_total


def get_history_late_overtime_hour(uid):
    late_hour_total = 0
    overtime_hour_total = 0
    start_date = datetime.datetime.strptime("2015-06", "%Y-%m")
    today = datetime.datetime.now()

    date = start_date

    while date <= today:
        the_month = date.strftime("%Y-%m")
        late_hour, overtime_hour = get_late_overtime_hour(uid, the_month)
        late_hour_total += late_hour
        overtime_hour_total += overtime_hour
        year = date.year
        month = date.month

        # print "%s-%0.2d %2d %2d" % (year, month, late_hour, overtime_hour)

        year = year + 1 if month == 12 else year
        month = month + 1 if month < 12 else 1

        date = datetime.datetime.strptime("{year}-{month}".format(year=year, month=month), "%Y-%m")

    return late_hour_total, overtime_hour_total


def set_attendance_status_on_check_out(session, attendance):
    """ Set attendance status when user check out

    :param session: db session
    :param attendance: Attendance class
    """
    date = datetime.datetime.strptime(attendance.date, "%Y-%m-%d")
    if date.weekday() in [5, 6]:
        # 周末来打下班卡，好孩子！
        # ~\(≧▽≦)/~
        attendance.attendance_status = 10
    else:
        # 平时打下班卡
        if attendance.check_in > attendance.legal_check_in:
            if attendance.check_out < attendance.legal_check_out:
                # 迟到且早退
                attendance.attendance_status = 8
                attendance.is_maintainable = 2
            else:
                # 迟到
                attendance.attendance_status = 6
                attendance.is_maintainable = 2
        else:
            if attendance.check_out < attendance.legal_check_out:
                # 早退
                attendance.attendance_status = 7
                attendance.is_maintainable = 2
            else:
                # 正常
                attendance.attendance_status = 2
    session.commit()


def set_attendance_status_daily(date=""):
    """ A function that runs once a day, in order to set user's attendance attendance

    If user has checked out, set_attendance_status_on_check_out should be called.
    So this function should deal with illegal attendance, such as no_check_out, no_attendance_today, etc.
    """
    if not date:
        date = datetime.datetime.now().strftime("%Y-%m-%d")

    the_date = datetime.datetime.strptime(date, "%Y-%m-%d")

    default_check_time = datetime.datetime.strptime("{date}".format(date=date), "%Y-%m-%d")

    session = DB_Session()
    users = session.query(User).filter(
        User.is_present == 1,
        User.is_admin == 0
    ).order_by(User.id).all()

    for user in users:
        try:
            # 用户当天有打卡记录，说明来打过上班卡
            attendance = session.query(Attendance).filter(
                Attendance.userid == user.id,
                Attendance.date == date
            ).one()
            if attendance.attendance_status == 1:
                # 状态为待定，说明还没打下班卡
                attendance.check_out = default_check_time
                attendance.is_maintainable = 2
                if the_date.weekday() in [5, 6]:
                    # 周末加班忘打下班卡……
                    # 只能算作没加班了……
                    # ╮(╯▽╰)╭
                    attendance.attendance_status = 2
                else:
                    attendance.attendance_status = 9
            else:
                # 用户的状态已经计算过了，忽略
                pass
        except sqlalchemy.orm.exc.NoResultFound:
            # 没有找到用户当天的打卡记录
            # 需要强势插入一条记录！
            legal_check_in = datetime.datetime.strptime(
                "{date} {time}".format(date=date, time=user.banci), "%Y-%m-%d %H:%M"
            )
            legal_check_out = legal_check_in + datetime.timedelta(hours=9)
            attendance = Attendance(
                userid=user.id,
                legal_check_in=legal_check_in,
                legal_check_out=legal_check_out,
                date=date,
                check_in=default_check_time,
                check_out=default_check_time,
                updatetime=datetime.datetime.now()
            )
            if the_date.weekday() in [5, 6]:
                # 周末未打卡，正常
                attendance.is_maintainable = 1
                attendance.attendance_status = 2
            else:
                # 工作日未打卡，得多大心啊...
                attendance.is_maintainable = 2
                attendance.attendance_status = 9
            session.add(attendance)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            # 找到当天有多条打卡记录
            # todo
            pass

    session.commit()
    session.close()


def update_attendance_status(uid):
    """ Run this method after initialize new database

    Run set_legal_check first!
    """
    session = DB_Session()
    user = session.query(User).filter(
        User.id == uid
    ).one()
    attendances = session.query(Attendance).filter(
        Attendance.userid == user.id
    ).all()
    for attendance in attendances:
        the_date = datetime.datetime.strptime(attendance.date, "%Y-%m-%d")
        if the_date.weekday() in [5, 6]:
            if attendance.check_in is not None and attendance.check_out is not None:
                attendance.attendance_status = 10
            else:
                attendance.attendance_status = 2
        else:
            if attendance.check_in is None or attendance.check_out is None:
                attendance.attendance_status = 9
            else:
                if attendance.check_in > attendance.legal_check_in:
                    if attendance.check_out < attendance.legal_check_out:
                        attendance.attendance_status = 8
                    else:
                        attendance.attendance_status = 6
                else:
                    if attendance.check_out < attendance.legal_check_out:
                        attendance.attendance_status = 7
                    else:
                        attendance.attendance_status = 2
    session.commit()

if __name__ == "__main__":
    print get_late_overtime_hour(6, "2015-10")
    print get_history_late_overtime_hour(6)
    # set_attendance_status_daily("2015-10-22")
    # set_legal_check(7)
    # update_attendance_status(7)
    # session = DB_Session()
    # attendance = session.query(Attendance).filter(
    #     Attendance.id == 8888
    # ).one()
    # set_attendance_status_on_check_out(session, attendance)
    # print get_late_overtime_hour(6, "2015-08")
    # for i in range(1, 31):
    #     set_attence_status(6, "2015-10-%0.2d" % i)
    # set_attence_status(37, "2015-07-19")
    # set_attence_status(37, "2015-07-20")
    # set_attence_status(37, "2015-07-21")
    # set_attence_status(37, "2015-07-22")
    # set_attence_status(37, "2015-07-23")
    # set_attence_status(37, "2015-07-24")
    # set_attence_status(37, "2015-07-25")
    # set_attence_status(37, "2015-07-26")
    # set_attence_status(6, "2015-10-18")



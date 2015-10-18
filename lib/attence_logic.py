# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import datetime

import sqlalchemy.orm.exc

from lib.models import User, Attence, ModifyAttence
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

    attences = session.query(Attence).filter(
        Attence.userid == user.id
    )
    for attence in attences:
        if attence.legal_checkin is not None:
            print "legal_checkin already set @ %s" % attence.legal_checkin
        else:
            attence.legal_checkin = datetime.datetime.strptime(
                "{date} {time}".format(date=attence.date, time=user.banci),
                "%Y-%m-%d %H:%M"
            )
        attence.legal_checkout = attence.legal_checkin + datetime.timedelta(hours=9)

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

    try:
        user = session.query(User).filter(
            User.id == uid,
            User.is_present == 1
        ).one()
    except sqlalchemy.orm.exc.NoResultFound:
        print "uid %s not found" % uid
        return 0
    except sqlalchemy.orm.exc.MultipleResultsFound:
        print "multiple uid %s found" % uid
        return 0

    attences = session.query(Attence).filter(
        Attence.userid == user.id,
        Attence.date.like("{month}%".format(month=month))
    ).order_by(Attence.date).all()

    if not attences:
        return 0

    for attence in attences:
        late_hour = 0
        overtime_hour = 0

        print attence.date
        if attence.status == u'全天请假':
            pass
        elif attence.status == u'旷工':
            late_hour = 8
        elif datetime.datetime.strptime(attence.date, "%Y-%m-%d").weekday() not in [5, 6]:
            if attence.status == u'上半天请假':
                legal_checkin = attence.legal_checkin + datetime.timedelta(hours=5)
                legal_checkout = attence.legal_checkout
            elif attence.status == u'下半天请假':
                legal_checkin = attence.legal_checkin
                legal_checkout = attence.legal_checkin + datetime.timedelta(hours=5)
            else:
                legal_checkin = attence.legal_checkin
                legal_checkout = attence.legal_checkout

            if attence.login > legal_checkin:   # 打卡时间晚于上班时间
                late_hour += (attence.login - attence.legal_checkin).seconds / 3600 + 1
            if attence.logout < legal_checkout:     # 打卡时间早于下班时间
                late_hour += (attence.legal_checkout - attence.logout).seconds / 3600 + 1
            overtime_hour += (attence.logout - attence.legal_checkout).seconds / 3600
        elif attence.logout is not None:
            overtime_hour = (attence.logout - attence.login).seconds / 3600

        # if attence.status == u'迟到':
        #     late_seconds = (attence.login - attence.legal_checkin).seconds
        #     late_hour = late_seconds / 3600 + 1     # 缺勤不足一小时按一小时算
        #     overtime_seconds = (attence.logout - attence.legal_checkout).seconds
        #     overtime_hour = overtime_seconds / 3600     # 加班需要满一小时才算数
        # elif attence.status == u'早退':
        #     late_seconds = (attence.legal_checkout - attence.logout).seconds
        #     late_hour = late_seconds / 3600 + 1
        # elif attence.status == u'迟到且早退':
        #     morning_late_seconds = (attence.login - attence.legal_checkin).seconds
        #     morning_late_hour = morning_late_seconds / 3600 + 1
        #     evening_late_seconds = (attence.legal_checkout - attence.logout).seconds
        #     evening_late_hour = evening_late_seconds / 3600 + 1
        #     late_hour = morning_late_hour + evening_late_hour
        # elif attence.status in [u'旷工', u'已拒绝']:
        #     # 审批没通过的考勤，按照旷工算
        #     late_hour = 8
        # elif attence.status == u'周末加班':
        #     overtime_seconds = (attence.logout - attence.login).seconds
        #     overtime_hour = overtime_seconds / 3600
        # else:
        #     # 正常，已通过
        #     if datetime.datetime.strptime(attence.date, "%Y-%m-%d").weekday() not in [5, 6]:
        #         # 工作日的正常/已通过
        #         overtime_seconds = (attence.logout - attence.legal_checkout).seconds
        #         overtime_hour = overtime_seconds / 3600
        #     else:
        #         # 周末的正常，应该没有上下班打卡
        #         # 周末的已通过，有上下班打卡
        #         if attence.login:
        #             overtime_seconds = (attence.logout - attence.login).seconds
        #             overtime_hour = overtime_seconds / 3600
        #         else:
        #             pass

        # print attence.date, late_hour, overtime_hour

        late_hour_total += late_hour
        overtime_hour_total += overtime_hour

    session.close()
    return late_hour_total, overtime_hour_total


def set_attence_status(uid, date):
    """ Set user(id = uid) attence status on date.
    :param date: format yyyy-mm-dd

    This function should run once a day!
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

    check_date = datetime.datetime.strptime(date, "%Y-%m-%d")
    legal_checkin = datetime.datetime.strptime(
        "{date} {time}".format(date=date, time=user.banci), "%Y-%m-%d %H:%M"
    )
    legal_checkout = legal_checkin + datetime.timedelta(hours=9)

    try:
        # date日期下有一条uid的考勤记录，用户打过上班卡了
        attence = session.query(Attence).filter(
            Attence.userid == uid,
            Attence.date == date
        ).one()

        if check_date.weekday() in [5, 6]:
            # 周六、周日有记录，说明来上过班
            if attence.logout is None:
                # 用户忘打下班卡了，只能算是没加班了
                # ╮(￣▽￣")╭
                attence.status = u"正常"
            else:
                attence.status = u"周末加班"
        else:
            # 工作日有打卡记录，正常上班
            if attence.logout is None:
                # 用户忘打下班卡了，只能算是旷工
                # ╮(￣▽￣")╭
                attence.status = u"旷工"
            elif attence.login > legal_checkin:
                if attence.logout > legal_checkout:
                    attence.status = u"迟到"
                else:
                    attence.status = u"迟到且早退"
            elif attence.logout < legal_checkout:
                attence.status = u"早退"
            else:
                attence.status = u"正常"
    except sqlalchemy.orm.exc.NoResultFound:
        # date日期下没有uid的考勤记录
        # 说明用户当天没有打上班卡
        # 系统给用户生成一条考勤记录
        attence = Attence(
            userid=uid,
            login=datetime.datetime.strptime(date, "%Y-%m-%d"),
            logout=datetime.datetime.strptime(date, "%Y-%m-%d"),
            date=date,
            updatetime=datetime.datetime.now(),
            legal_checkin=legal_checkin,
            legal_checkout=legal_checkout
        )

        if check_date.weekday() in [5, 6]:
            # 周六、周日没有考勤记录，属于正常现象
            attence.status = u"正常"
        else:
            # 工作日没有考勤记录，属于旷工
            attence.status = u"旷工"
        session.add(attence)
    except sqlalchemy.orm.exc.MultipleResultsFound:
        # date日期下有多条uid的考勤记录
        print "Multiple attence records found on uid %s @ %s" % (uid, date)
        return None

    # 处理完毕，提交到数据库
    session.commit()
    session.close()
    return True


if __name__ == "__main__":
    print get_late_overtime_hour(6, "2015-08")
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
    # set_legal_check(6)
    # set_attence_status(6, "2015-10-18")



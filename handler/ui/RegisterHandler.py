# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import datetime

import sqlalchemy.orm.exc

from handler.BaseHandler import BaseHandler
from lib.models import User, Company, Team


class RegisterHandler(BaseHandler):
    """
    url pattern: /register/
    """

    def get(self, *args, **kwargs):
        """
        显示注册页面
        """
        companies = self.session.query(Company).order_by(Company.id).all()
        teams = self.session.query(Team).order_by(Team.id).all()

        if self.current_user:
            self.redirect(self.get_argument("next", "/"))
        else:
            self.render("register.html", error="", companies=companies, teams=teams)

    def post(self, *args, **kwargs):
        """
        处理用户提交的注册表单
        """
        name = self.get_argument("user-name")
        email = self.get_argument("user-email")
        pwd = self.get_argument("user-pwd")
        worktime = self.get_argument("user-worktime")
        company = self.get_argument("user-company")
        team = self.get_argument("user-team")

        companies = self.session.query(Company).order_by(Company.id).all()
        teams = self.session.query(Team).order_by(Team.id).all()
        row2dict = lambda rows: {row.name: row.id for row in rows}

        company_dict = row2dict(companies)
        team_dict = row2dict(teams)

        if not name:
            self.render("register.html", error="姓名不能为空", companies=companies, teams=teams)
        if not email:
            self.render("register.html", error="邮箱不能为空", companies=companies, teams=teams)
        if not pwd:
            self.render("register.html", error="密码不能为空", companies=companies, teams=teams)
        if not worktime:
            self.render("register.html", error="上班时间不能为空", companies=companies, teams=teams)
        if company not in company_dict.keys():
            self.render("register.html", error="公司不存在啊亲~", companies=companies, teams=teams)
        if company_dict[company] == 1:
            self.render("register.html", error="请选择公司", companies=companies, teams=teams)
        if team not in team_dict.keys():
            self.render("register.html", error="工作组不存在啊亲~", companies=companies, teams=teams)
        if team_dict[team] == 1:
            self.render("register.html", error="请选择工作组", companies=companies, teams=teams)

        email += '@qiyi.com'

        try:
            self.session.query(User).filter(
                User.email == email,
                User.is_present == 1
            ).one()
            self.render("register.html", error="邮箱{email}已被注册，请确认邮箱后重试".format(email=email))
        except sqlalchemy.orm.exc.NoResultFound:
            user = User(
                name=name,
                email=email,
                passcode=pwd,
                banci=worktime,
                company=company_dict[company],
                team=team_dict[team],
                createdate=datetime.datetime.now()
            )
            self.session.add(user)
            self.session.commit()
            self.set_secure_cookie("uid", str(user.id))
            self.redirect(self.get_argument("next", "/"))
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("找到多个在职的{email}，请联系songbowen@qiyi.com".format(email=email))


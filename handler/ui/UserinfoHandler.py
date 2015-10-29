# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import tornado.web
import sqlalchemy.orm.exc

from handler.BaseHandler import BaseHandler
from lib.models import User, Company, Team


class UserinfoHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, *args, **kwargs):
        companies = self.session.query(Company).order_by(Company.id).all()
        teams = self.session.query(Team).order_by(Team.id).all()
        try:
            user = self.session.query(User).filter(
                User.id == self.current_user,
                User.is_present == 1
            ).one()
            self.render("userinfo.html", current_user=user, active_tag="userinfo", companies=companies, teams=teams)
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("uid %s not found" % self.current_user)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)

    @tornado.web.authenticated
    def post(self, *args, **kwargs):
        name = self.get_argument("user-name")
        email = self.get_argument("user-email") + "@qiyi.com"
        pwd = self.get_argument("user-pwd")
        worktime = self.get_argument("user-worktime")
        company = self.get_argument("user-company")
        team = self.get_argument("user-team")

        companies = self.session.query(Company).order_by(Company.id).all()
        teams = self.session.query(Team).order_by(Team.id).all()
        row2dict = lambda rows: {row.name: row.id for row in rows}
        company_dict = row2dict(companies)
        team_dict = row2dict(teams)

        try:
            user = self.session.query(User).filter(
                User.id == self.current_user,
                User.is_present == 1
            ).one()
            user.name = name
            user.email = email
            user.passcode = pwd
            user.banci = worktime
            user.company = company_dict[company]
            user.team = team_dict[team]
            self.session.commit()
            self.render("userinfo.html", current_user=user, active_tag="userinfo", companies=companies, teams=teams)
        except sqlalchemy.orm.exc.NoResultFound:
            self.finish("uid %s not found" % self.current_user)
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.finish("multiple uid %s found" % self.current_user)


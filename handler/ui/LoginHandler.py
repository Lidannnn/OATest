# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import sqlalchemy.orm.exc

from handler.BaseHandler import BaseHandler
from lib.models import User


class LoginHandler(BaseHandler):
    """
    url pattern: /login/
    """

    def get(self, *args, **kwargs):
        if self.is_admin():
            self.redirect("/admin/")
        elif self.current_user:
            self.redirect("/")

        self.render("login.html", error="")

    def post(self, *args, **kwargs):
        """
        处理用户提交的登陆表单
        """
        email = self.get_argument("name") + "@qiyi.com"
        password = self.get_argument("pwd")

        try:
            remember = self.get_argument("remember")
        except:
            remember = False

        try:
            user = self.session.query(User).filter(
                User.email == email,
                User.is_present == 1
            ).one()

            if user.passcode != password:
                # 密码错误
                self.render("login.html", error="wrong password")

            if remember:
                # 勾选记住我
                self.set_secure_cookie("uid", str(user.id), expires_days=7)
            else:
                self.set_secure_cookie("uid", str(user.id), expires_days=1)

            self.current_user = str(user.id)

            if self.is_admin():
                self.redirect(self.get_argument("next", "/admin/"))
            elif not user.team or not user.company:
                self.redirect(self.get_argument("next", "/userinfo/"))
            else:
                self.redirect(self.get_argument("next", "/"))

        except sqlalchemy.orm.exc.NoResultFound:
            self.render("login.html", error=u"{email}没有找到。请先注册再登陆".format(email=email))
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.render("login.html", error=u"{email}找到多个。请联系songbowen@qiyi.com".format(email=email))






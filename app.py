# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import os

import tornado.httpserver
import tornado.ioloop
import tornado.web

from url import url_pattern


class Application(tornado.web.Application):
    def __init__(self):
        handlers = url_pattern
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "template"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
            login_url="/login/",
            cookie_secret="W34+Q82GQ8yQo6Di/V5R/VrAK4enekGdkZj9elsFJP8="
        )
        tornado.web.Application.__init__(self, handlers=handlers, **settings)


if __name__ == "__main__":
    server = tornado.httpserver.HTTPServer(Application())
    server.listen(2735)
    tornado.ioloop.IOLoop.current().start()

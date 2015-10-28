# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import os

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import options, define

from url import url_pattern


prj_root_dir = os.path.dirname(os.path.dirname(__file__))
define("log_rotate_when", default="midnight")
define("log_rotate_mode", default="time")


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
    # enable log here
    options.logging = "debug"
    options.log_file_prefix = os.path.join(prj_root_dir, "log/log.log")
    tornado.log.enable_pretty_logging(options)

    server = tornado.httpserver.HTTPServer(Application())
    server.listen(2735)
    tornado.ioloop.IOLoop.current().start()

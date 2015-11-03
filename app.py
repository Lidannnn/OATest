# -*- coding: utf-8 -*-
__author__ = 'songbowen'

import os

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.log
from tornado.log import access_log
from tornado.options import options

from url import url_pattern


prj_root_dir = os.path.dirname(os.path.dirname(__file__))


def log_function(handler):
    if handler.get_status() < 400:
        log_method = access_log.info
    elif handler.get_status() < 500:
        log_method = access_log.warning
    else:
        log_method = access_log.error
    request_time = 1000.0 * handler.request.request_time()
    log_method("%d %s %s %s %.2fms", handler.get_status(),
               handler._request_summary(),
               handler.request.body_arguments if handler.request.method == "POST" else "",
               handler.request.cookies,
               request_time)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = url_pattern
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "template"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
            login_url="/login/",
            cookie_secret="W34+Q82GQ8yQo6Di/V5R/VrAK4enekGdkZj9elsFJP8=",
            log_function=log_function
        )
        tornado.web.Application.__init__(self, handlers=handlers, **settings)


if __name__ == "__main__":
    # enable log here
    options.logging = "debug"
    options.log_file_prefix = os.path.join(prj_root_dir, "log/log.log")
    tornado.log.enable_pretty_logging(options)

    server = tornado.httpserver.HTTPServer(Application())
    server.listen(9876)
    tornado.ioloop.IOLoop.current().start()

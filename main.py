from pymongo import MongoClient
import tornado.ioloop
import tornado.web
import logging
import redis
import sys
import os
import settings


logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.warn = lambda x: logging.Logger.warn(logger, u'\033[1;31m%s\033[0m' % x)


def import_apps():

    """
    import all apps from ./apps/
    """

    apps_path = os.path.abspath(os.path.dirname(__file__)) + '/apps'
    app_list = os.listdir(apps_path)
    for app in app_list:
        if app.startswith('__'):
            continue

        api_list = os.listdir(apps_path + '/' + app)
        for api in api_list:
            if not api.endswith('.py'):
                continue
            module = __import__('apps.%s.%s' % (app, api[:-3]), globals(), locals(), ['*'], 0)
            for k in dir(module):
                if k.startswith('__'):
                    continue

                m = getattr(module, k)
                if hasattr(m, 'SUPPORTED_METHODS') or k == 'route':
                    globals()[k] = m


def str_json(obj):
    if type(obj) is dict:
        return {k: str_json(v) for k, v in obj.items()}
    if type(obj) is list:
        return [str_json(i) for i in obj]
    if type(obj) in [int, float]:
        return obj
    return str(obj)


class route(object):

    """
    url route
    """

    routes = []

    def __init__(self, uri):
        self.uri = uri

    def __call__(self, handler):

        """
        use as decorate
        """

        self.routes.append((self.uri, handler))
        return handler

    @classmethod
    def get_routes(self):

        """
        :rtype: list of all route
        """

        return self.routes


rd = redis.Redis(host=settings.RD_HOST, port=settings.RD_PORT, db=settings.RD_DB)
db = MongoClient()[settings.PROJECT_NAME]


class BaseHandler(tornado.web.RequestHandler):

    """
    all handler should inherit from here
    """

    rd = rd
    db = db
    logger = logger

    def initialize(self):
        
        if self.settings.get('debug'):
            # for test
            self.logger.info("\n\033[1;31m%s\033[0m" % ('=' * 60))
            import json
            for i in [self.request.headers, self.request.arguments]:
                self.logger.info(json.dumps({k: ''.join(map(lambda x: x if type(x) is str else x.decode(), v)) for k, v in i.items()}, indent=2))
                self.logger.info("\033[1;34m%s\033[0m" % '-' * 60)
            self.logger.info(self.request.remote_ip)

    def write_json(self, obj):
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(str_json(obj))


if __name__ == "__main__":

    port = 8866 if len(sys.argv) == 1 else int(sys.argv[1])

    import_apps()
    ROOT = os.path.abspath(os.path.dirname(__file__))
    app = tornado.web.Application(
        route.get_routes(),
        debug=settings.DEBUG,
        cookie_secret = settings.COOKIE_SECRET,
        template_path = os.path.join(ROOT, "templates"),
        static_path = os.path.join(ROOT, "static")
    )
    app.listen(port, xheaders=True)
    logger.info("API server Starting on port %d" % port)

    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        logger.info("exiting...")
        sys.exit(0)

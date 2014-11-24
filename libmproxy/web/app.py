import os.path
import sys
import tornado.web
import tornado.websocket
import logging
import json
from .. import filt, flow


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class ClientConnection(tornado.websocket.WebSocketHandler):
    connections = set()

    def open(self):
        ClientConnection.connections.add(self)

    def on_close(self):
        ClientConnection.connections.remove(self)

    @classmethod
    def broadcast(cls, type, data):
        for conn in cls.connections:
            try:
                conn.write_message(
                    json.dumps(
                        {
                            "type": type,
                            "data": data
                        }
                    )
                )
            except:
                logging.error("Error sending message", exc_info=True)


class FlowViewConnection(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(FlowViewConnection, self).__init__(*args, **kwargs)
        self.view = None

    def open(self):
        start = int(self.get_argument("start", 0))
        count = int(self.get_argument("count", sys.maxint))
        filtstr = self.get_argument("filt", "")
        sortstr = self.get_argument("sort", None)

        filtfun = filt.parse(filtstr)
        sortfun = dict(
            size=flow.sort_by_size
        ).get(sortstr, flow.default_sort)

        state = self.application.state
        self.view = state.flows.open_view(self, start, count, filtfun, sortfun)

    def on_close(self):
        state = self.application.state
        state.flows.close_view(self.view)


class Application(tornado.web.Application):
    def __init__(self, state, debug):
        self.state = state
        handlers = [
            (r"/", IndexHandler),
            (r"/updates", ClientConnection),
            (r"/flowview", FlowViewConnection),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            debug=debug,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


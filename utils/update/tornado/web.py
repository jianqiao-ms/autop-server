#!/usr/bin/env python3
import utils.configuration
import logging
from typing import (
    Dict,
    Any,
    Union,
    Optional,
    Awaitable,
    Tuple,
    List,
    Callable,
    Iterable,
    Generator,
    Type,
    cast,
    overload,
)

from tornado.concurrent import Future, future_set_result_unless_cancelled
import tornado.web



class Application(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)



class RequestHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        super(RequestHandler, self).__init__(*args, **kwargs)



class RestRequestHandler(RequestHandler):
    def initialize(self) -> None:
        self.response = dict(
            errcode = 0,
            errmsg = ""
        )

    async def finish(self, chunk: Optional[Union[dict]] = None) -> "Future[None]":
        # errcode = chunk.pop("errcode", 0)
        # errmsg = chunk.pop("errmsg", "")
        if chunk:
            self.response.update(**chunk)
        await super(RestRequestHandler, self).finish(self.response)

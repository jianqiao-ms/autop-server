#!/usr/bin/env python3
import functools
import logging
import os
import uuid
from typing import (
    AnyStr, Dict
)

import tornado.httpclient
import tornado.ioloop
import tornado.iostream

from orm import ModelKubernetes

from utils.api_client import ClientKubernetes


class Task(object):
    def __init__(self, *args, **kwargs):
        self.id = kwargs.pop("id", str(uuid.uuid4()))
        self.type = kwargs.pop("type", str(uuid.uuid4()))
        if not self.type:
            raise Exception("Task must init attribute \"type\"")
        # super(Task, self).__init__(*args, **kwargs)


    def run(self):
        raise NotImplemented



class OneshotTask(Task):
    def __init__(self, *args, **kwargs):
        kwargs["type"] = "OneshotTask"
        super(OneshotTask, self).__init__(*args, **kwargs)



class CronTask(Task):
    def __init__(self, *args, **kwargs):
        kwargs["type"] = "CronTask"
        self.life = kwargs.pop("life", 600)
        super(CronTask, self).__init__(*args, **kwargs)



class ForeverTask(Task):
    def __init__(self, *args, **kwargs):
        kwargs["type"] = "ForeverTask"
        super(ForeverTask, self).__init__(*args, **kwargs)



# class HTTPWatchTask(ForeverTask):
#     def __init__(self, *args, **kwargs):
#         kwargs["type"] = "HTTPWatchTask"
#         self.url:AnyStr = NotImplemented
#         self.headers:Dict = NotImplemented
#         super(HTTPWatchTask, self).__init__(*args, **kwargs)
#
#     def stream_handler(self, chunk):
#         raise NotImplemented
#
#     def start(self):
#         r, w = os.pipe()
#         rs = tornado.iostream.PipeIOStream(r)
#         ws = tornado.iostream.PipeIOStream(w)
#
#         def stream_handler(fd:tornado.iostream.PipeIOStream, event:int):
#             def set_json(future):
#                 global json
#                 logging.debug("Test Streaming Callback: %s" % (future.result()))
#             tornado.ioloop.IOLoop.current().add_future(fd.read_until(b'\n'), set_json)
#
#         tornado.ioloop.IOLoop.current().add_handler(rs, stream_handler, tornado.ioloop.IOLoop.READ)
#         tornado.httpclient.AsyncHTTPClient().fetch(self.url,
#                                                    headers = self.headers,
#                                                    request_timeout=0)


class KubernetesWatchTask(ForeverTask):
    def __init__(self, *args, **kwargs):
        ForeverTask.__init__(self, *args, **kwargs)

        self.kubernetes = kwargs.get("kubernetes", None)
        self.api_request:tornado.httpclient.HTTPRequest = kwargs.get("api_request", None)
        self.resource = kwargs.get("resource", None)

        r, w = os.pipe()
        rs = tornado.iostream.PipeIOStream(r)
        ws = tornado.iostream.PipeIOStream(w)

        self.buffer = ws
        self.cache = rs

        self.start()

    def watch_handler(self, fd, event):
        watch_event_data = fd.read_until(b"\n").result()
        # logging.debug("Receive kubernetes watch event: %s" % (watch_event_data))

    def start(self):
        self.api_request.streaming_callback = self.buffer.write
        self.api_request.request_timeout = 0

        tornado.httpclient.AsyncHTTPClient().fetch(self.api_request)
        tornado.ioloop.IOLoop.current().add_handler(self.cache, self.watch_handler, tornado.ioloop.IOLoop.READ)

class TaskManager():
    def __init__(self, *args, **kwargs):
        self.task_list = []

    def add_task(self, task):
        self.task_list.append(task)
        task.start()

    def list_tasks(self):
        return self.task_list

    async def boot_cron_tasks(self):
        kuberetes_list = await ModelKubernetes.filter(namespace_watch=True).all()
        for kuberetes in kuberetes_list:
            self.add_task(KubernetesWatchTask(**kuberetes.dict()))



task_manager = TaskManager()

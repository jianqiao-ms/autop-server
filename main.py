#!/usr/bin/env python3
import logging
import utils

import tornado.ioloop


from utils.update.tornado import Application
from utils.task import task_manager
from handlers.kubernetes import HandlerKubernetes
from handlers.kubernetes import HandlerNamespace
from handlers.kubernetes import HandlerDeployment
from handlers.kubernetes import HandlerContainer

from handlers.application import HandlerApplication



app = Application([
    ("/api/application", HandlerApplication),

    # ("/api/kubernetes/container", HandlerContainer),
    # ("/api/kubernetes/deployment", HandlerDeployment),
    # ("/api/kubernetes/namespace", HandlerNamespace),
    ("/api/kubernetes/(?P<id>[\d\w\-]+)/(?P<resource>[\d\w\-]+)/(?P<operation>[\d\w\-]+)", HandlerKubernetes),
    ("/api/kubernetes", HandlerKubernetes)
], **dict(
    debug = utils.configuration["autop"]["debug"]
))

if __name__ == '__main__':
    app.listen(8888)
    # tornado.ioloop.IOLoop.current().spawn_callback(task_manager.boot_cron_tasks)
    tornado.ioloop.IOLoop.current().start()

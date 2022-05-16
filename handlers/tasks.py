#!/usr/bin/env python3

from utils.update.tornado import RequestHandler
from utils.task import task_manager



class HandlerTasks(RequestHandler):
    async def get(self):
        response = {
            "errcode": 0,
            "errmsg": "",
            "target": {}
        }
        for task in task_manager.task_dict:
            response["target"][task.id] = task.__dict__
        await self.finish(response)

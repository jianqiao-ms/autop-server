#!/usr/bin/env python3
import logging

from tornado.escape import json_encode, json_decode
from sqlalchemy.future import select
from sqlalchemy.sql import and_

from utils.update.tornado import RequestHandler, RestRequestHandler
from utils.task import task_manager
# from utils.task import KubernetesNamespaceWatchTask

from orm import async_session
from orm import ModelKubernetes, ModelKubernetesNamespace, ModelKubernetesDeployment, ModelKubernetesContainer
# from tortoise.query_utils import Prefetch



class HandlerApplication(RestRequestHandler):
    async def get(self):
        async with async_session() as session:
            statement = select(ModelKubernetesContainer).join(
                ModelKubernetesDeployment,
                ModelKubernetesDeployment.id == ModelKubernetesContainer.controller_id,
                isouter=True
            ).join(
                ModelKubernetesNamespace,
                ModelKubernetesDeployment.namespace_id == ModelKubernetesNamespace.id,
                isouter=True
            ).where(and_(
                ModelKubernetesContainer.controller_type == "deployment",
                ModelKubernetesNamespace.name == "mall",
                ModelKubernetesNamespace.is_business == True
            ))
            applications = list(map(lambda x:x.serialize(), (await session.execute(statement)).scalars()))
        await self.finish({"applications": applications})



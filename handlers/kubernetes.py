#!/usr/bin/env python3
import json
import logging
import tornado.httpclient

from tornado.escape import json_encode, json_decode
from sqlalchemy.future import select

from utils.update.tornado import RequestHandler, RestRequestHandler
from utils.task import task_manager
from utils.task import KubernetesWatchTask
from utils.api_client import ClientKubernetes, ArgumentNotImplement, NotSupportedOperation

from orm import async_session
from orm import ModelKubernetes, ModelKubernetesNamespace, ModelKubernetesDeployment, ModelKubernetesContainer
# from tortoise.query_utils import Prefetch


class HandlerContainer(RestRequestHandler):
    async def get(self):
        async with async_session() as session:
            statement = select(ModelKubernetesContainer)
            containers = list(map(lambda x:x.serialize(), (await session.execute(statement)).scalars()))
        await self.finish({"containers": containers})



class HandlerDeployment(RestRequestHandler):
    async def get(self):
        async with async_session() as session:
            statement = select(ModelKubernetesDeployment)
            deployments = list(map(lambda x:x.serialize(), (await session.execute(statement)).scalars()))
        await self.finish({"deployments": deployments})



class HandlerNamespace(RestRequestHandler):
    async def get(self):
        async with async_session() as session:
            statement = select(ModelKubernetesNamespace)
            namespaces = list(map(lambda x:x.serialize(), (await session.execute(statement)).scalars()))
        print(namespaces)
        await self.finish({"namespaces": namespaces})


class HandlerKubernetes(RestRequestHandler):
    @staticmethod
    def modal_serialize(kubernetes_modal: ModelKubernetes):
        return dict(
            id=kubernetes_modal.id,
            name=kubernetes_modal.name,
            address=kubernetes_modal.address,
            port=kubernetes_modal.port,
        )

    async def get(self):
        async with async_session() as session:
            statement = select(ModelKubernetes)
            kubernertes = list(map(lambda x: self.modal_serialize(x), (await session.execute(statement)).scalars()))
        await self.finish({"kubernertes": kubernertes})

    async def post(self, id, resource, operation): # proxy kubernetes rest apis
        logging.debug("Executing %s on %s of kubernetes %s" %(operation, resource, id))
        request_body = json_decode(self.request.body) if self.request.body else {}
        # arguments = request_body.pop("arguments")
        # kubernetes_body = request_body.pop("kubernetes_body")
        async with async_session() as session:
            statement = select(ModelKubernetes).where(ModelKubernetes.id==id)
            kubernertes = (await session.execute(statement)).first()[0]
            kubernertes.__dict__.pop("_sa_instance_state")
            logging.debug("kubernetes record:%s" % json.dumps(kubernertes.__dict__, indent=2))
            client = ClientKubernetes(**dict(
                address = kubernertes.address,
                port = kubernertes.port,
                token = kubernertes.token
            ))
        logging.debug("Target kubernetes %s, address:%s" % (kubernertes.name, kubernertes.address))



        try:
            api_request:tornado.httpclient.HTTPRequest = client.__getattr__(resource).__getattr__(operation)(**request_body)
            if operation.startswith("watch"):
                task = KubernetesWatchTask(kubernetes=kubernertes, api_request=api_request, resource=resource,
                                           operation=operation)
                await self.finish(dict(
                    message="Create watch task ok.",
                    task=task.id
                ))

            response = await tornado.httpclient.AsyncHTTPClient().fetch(api_request)
            await self.finish(json_decode(response.body))
        except ArgumentNotImplement as e:
            await self.finish(dict(
                errcode = 10001,
                errmsg = e.args[0]
            ))
        except NotSupportedOperation as e:
            await self.finish(dict(
                errcode=10002,
                errmsg=e.args[0]
            ))
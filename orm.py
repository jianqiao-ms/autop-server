#!/usr/bin/env python3
import tornado.ioloop
import utils

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

from sqlalchemy import Column
from sqlalchemy import (
    DateTime,
    ForeignKey,
    func,
    Integer,
    String,
    Boolean
)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import sessionmaker

Base = declarative_base()



class ModelKubernetes(Base):
    __tablename__ = "kubernetes"

    id = Column(String(36), primary_key=True)
    name = Column(String(255))
    address = Column(String(255))
    port = Column(String(5))
    token = Column(String(2048))
    namespace_watch = Boolean()


    def serialize(self):
        return dict(
            id = self.id,
            name = self.name,
            address = self.address,
            port = self.port,
            token = self.token,
            namespace_watch = bool(self.namespace_watch)
        )


class ModelKubernetesNamespace(Base):
    __tablename__ = "kubernetes_namespace"

    id = Column(String(36), primary_key=True)
    uid = Column(String(36))
    kubernetes_id = Column(ForeignKey("kubernetes.id"))
    name = Column(String(255))
    deployment_watch = Boolean()
    pod_watch = Boolean()
    is_business = Column(Boolean())

    def serialize(self):
        return dict(
            id = self.id,
            uid = self.uid,
            kubernetes_id = self.kubernetes_id,
            name = self.name,
            deployment_watch = bool(self.deployment_watch),
            pod_watch = bool(self.pod_watch),
            is_business = bool(self.is_business)
        )



class ModelKubernetesDeployment(Base):
    __tablename__ = "kubernetes_deployment"

    id = Column(String(36), primary_key=True)
    uid = Column(String(36))
    namespace_id = Column(ForeignKey("kubernetes_namespace.id"))
    name = Column(String(255))
    pod_watch = Boolean()

    def serialize(self):
        return dict(
            id = self.id,
            uid = self.uid,
            namespace_id = self.namespace_id,
            name = self.name,
            pod_watch = bool(self.pod_watch)
        )



class ModelKubernetesContainer(Base):
    __tablename__ = "kubernetes_container"

    id = Column(String(36), primary_key=True)
    controller_type= Column(String(255))
    controller_id = Column(String(36))
    name = Column(String(255))

    def serialize(self):
        return dict(
            id = self.id,
            controller_type = self.controller_type,
            controller_id = self.controller_id,
            name = self.name,
        )




engine = create_async_engine(
    "mysql+aiomysql://{user}:{password}@{host}:{port}/{database}".format(**utils.configuration["mysql"]),
    echo=True,
)

async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

# async def init():
#     # Here we create a SQLite DB using file "db.sqlite3"
#     #  also specify the app name of "models"
#     #  which contain models from "app.models"
#     await Tortoise.init(
#         db_url='mysql://{user}:{password}@{host}:{port}/{database}'.format(**utils.configuration["mysql"]),
#         modules={'models': ['orm']}
#     )
#
#
# tornado.ioloop.IOLoop.current().run_sync(init)


# if __name__ == '__main__':
#     async def init():
#         # Here we create a SQLite DB using file "db.sqlite3"
#         #  also specify the app name of "models"
#         #  which contain models from "app.models"
#         await Tortoise.init(
#             db_url='mysql://{user}:{password}@{host}:{port}/{database}'.format(**utils.configuration["mysql"]),
#             modules={'models': ['__main__']}
#         )
#         print(ModelKubernetes.all())
#     run_async(init)



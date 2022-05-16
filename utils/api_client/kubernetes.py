#!/usr/bin/env python3
import json
import logging
import utils
import os
import re
import functools
import sys
from pathlib import Path

from yaml import load_all

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
import tornado.httpclient
import tornado.ioloop
import tornado.iostream
from tornado.concurrent import Future
from typing import AnyStr, Union


import unittest

KUBERNETES_API_REFERENCE_FILE = os.path.join(Path(__file__).parent.parent.parent, "api_reference_k8s.yaml")
kubernetes_api_reference = dict()
try:
    with open(KUBERNETES_API_REFERENCE_FILE, "r") as fp:
        api_docs = load_all(fp, Loader=Loader)
        for doc in api_docs:
            if doc["type"] == "kubernetes api description":
                if doc["version"] not in kubernetes_api_reference:
                    kubernetes_api_reference[doc["version"]] = doc["resources"]
            else:
                logging.warning("Duplicate version in kubernetes api reference: %s" % doc["version"])
except FileNotFoundError as e:
    logging.error("%s: %s" % (e.strerror, e.filename))
except Exception as e:
    logging.error(e)
    sys.exit(1)
kubernetes_api_reference_version_list: list = list(kubernetes_api_reference.keys())
kubernetes_api_reference_version_list.sort()



def get_kubernetes_api(version:AnyStr, resource:AnyStr, operation:AnyStr):
    if version in kubernetes_api_reference_version_list:
        kubernetes_version_index = kubernetes_api_reference_version_list.index(version)
    else:
        raise Exception("Not supported kubernetes version %s." % version)

    kubernetes_resource:Union[dict, None] = None
    for _version in kubernetes_api_reference_version_list[:kubernetes_version_index+1]:
        __kubernetes_resource:Union[dict, None] = kubernetes_api_reference[_version].get(resource, None)
        if __kubernetes_resource is None:
            continue
        if kubernetes_resource is None:
            kubernetes_resource = __kubernetes_resource
        else:
            kubernetes_resource.update(__kubernetes_resource)
    if kubernetes_resource is None:
        raise Exception("Not supported kubernetes resource:%s." % resource)
    logging.debug("%s api reference for current version: %s: \n%s" % (resource, version, json.dumps(kubernetes_resource,indent=2)))
    kubernetes_api = kubernetes_resource["operation"].get(operation, None)
    if kubernetes_api is None:
        raise Exception("Not supported operation %s for resource %s." % (operation, resource))
    group_and_version = dict(
        group=kubernetes_resource.get("group", None),
        version = kubernetes_resource.get("version")
    )
    if isinstance(kubernetes_api, str):
        kubernetes_api:dict = dict(uri = kubernetes_api,)
    kubernetes_api.update(group_and_version)
    return kubernetes_api



class IntermediaKubernetesResource(object):
    def __getattr__(self, item):
        return


class NotSupportedOperation(Exception):
    pass



class ArgumentNotImplement(Exception):
    pass



class KubernetesResource(object):
    __supported_operation__ = [
        "read", "list", "patch", "watch", "watch_list"
    ]

    def __init__(self, client, resource:AnyStr):
        self.client = client
        self.resource:AnyStr = resource

    def __getattr__(self, item): # item: kubernetes resource operation: read, list...etcd,.
        if item not in self.__supported_operation__:
            raise NotSupportedOperation("Not supported operation %s for resource %s." % (item, self.resource))
        self.resource_api = get_kubernetes_api(self.client.version, self.resource, item)
        logging.debug("Executing %s on resource %s" % (item, self.resource))
        logging.debug("%s %s api for current version %s: \n%s" % (self.resource, item, self.client.version, json.dumps(self.resource_api, indent=2)))
        return self.gen_request

    def call_api(self, *args, **kwargs) -> Future:  # initialize variables in api url
        return tornado.httpclient.AsyncHTTPClient().fetch(self.gen_request(*args, **kwargs))


    def gen_request(self, *args, **kwargs):
        streaming_callback = kwargs.pop("streaming_callback", None)
        arguments = kwargs.pop("arguments", {})
        kubernetes_body = kwargs.pop("kubernetes_body", None)
        __resource_api = "api"
        if self.resource_api.get("group"):
            __resource_api += "/%s" % self.resource_api.get("group")
        __resource_api += "/%s/%s" % (self.resource_api.get("version"), self.resource_api.get("uri").lstrip("/"))

        __resource_api = "https://%s:%s/%s" % (self.client.address, self.client.port, __resource_api)
        try:
            finnal_api = __resource_api.format(**arguments)
        except KeyError as e:
            raise ArgumentNotImplement('Arguments [%s] for api [%s] must be filled.' % (e.args[0], __resource_api))
        logging.debug("Calling kubernetes api: %s" % finnal_api)
        http_request = tornado.httpclient.HTTPRequest(finnal_api,
                                                      method=self.resource_api.get("method", "GET"),
                                                      body=kubernetes_body,
                                                      validate_cert=False,
                                                      headers={'Authorization': 'Bearer %s' % self.client.token},
                                                      streaming_callback=streaming_callback,
                                                      request_timeout=0 if streaming_callback else 5)
        return http_request


class ClientKubernetes(object):
    __supported_resource__ = [
        "namespace", "deployment", "ingress"
    ]
    def __init__(self, *args, **kwargs):
        self.address = kwargs.pop("address")
        self.port = kwargs.pop("port")
        self.token = kwargs.pop("token")
        self.version = kwargs.pop("version", "1.18")

    async def call_api(self, api, streaming_callback=None):
        logging.debug("Calling Kubernetes api: %s" % api)
        return tornado.httpclient.HTTPRequest(api, validate_cert=False, headers={'Authorization': 'Bearer %s' % self.token})


    def __getattr__(self, item):
        if item not in self.__supported_resource__:
            raise Exception("Not supported resource %s." % item)
        return KubernetesResource(self, item)


class ClientKubernetesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = ClientKubernetes(
            address="10.0.4.29",
            port="6443",
            token="eyJhbGciOiJSUzI1NiIsImtpZCI6Ii1XVzBHVHd2cmtTMVhCcGdQT3VzcGhZVzFnMnhqUXNhanVERmZsbmRVVHcifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJhdXRvcCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhdXRvcC10b2tlbi1id2dzdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJhdXRvcCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6ImI3NTU5ZWNiLTI5NTMtNDk5MS05NmZiLTFhYTBmMWY2N2Q2YSIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDphdXRvcDphdXRvcCJ9.slsEuWHlEIngnsAClSIyuMeSg5Dy9eu2Qfbozi7pB4-dJgEMLvoUsBnuVuvktkjWtRdf_tVwRU2gGPS2pUixjdoNHpUx4yWazriLdvN1w4eIl1DfHPFXZMDXUFTUQnAydXUq6fdge7B4n4zc3EEOsMbXKOY7PeHtGclrDcLp_fWS-dtkZQ0O54zLtK9f0aZ6xhFb0RkugxTMnSRCx32NTpZecKGipoGWfz_OGmuHsfWy0H4SZwH6MZVJ52nu7nCuJN0BnFWMtN7mA1ASblLH7zsJvqT6DKqi42_SXLjdi_2xF8o1-3jTasAbslRUgJPcOBH6VdYlmeWLjcxEDpemsA"
        )


if __name__ == '__main__':
    # unittest.main()

    client = ClientKubernetes(
        address="10.0.4.29",
        port="6443",
        token="eyJhbGciOiJSUzI1NiIsImtpZCI6Ii1XVzBHVHd2cmtTMVhCcGdQT3VzcGhZVzFnMnhqUXNhanVERmZsbmRVVHcifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJhdXRvcCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhdXRvcC10b2tlbi1id2dzdCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJhdXRvcCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6ImI3NTU5ZWNiLTI5NTMtNDk5MS05NmZiLTFhYTBmMWY2N2Q2YSIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDphdXRvcDphdXRvcCJ9.slsEuWHlEIngnsAClSIyuMeSg5Dy9eu2Qfbozi7pB4-dJgEMLvoUsBnuVuvktkjWtRdf_tVwRU2gGPS2pUixjdoNHpUx4yWazriLdvN1w4eIl1DfHPFXZMDXUFTUQnAydXUq6fdge7B4n4zc3EEOsMbXKOY7PeHtGclrDcLp_fWS-dtkZQ0O54zLtK9f0aZ6xhFb0RkugxTMnSRCx32NTpZecKGipoGWfz_OGmuHsfWy0H4SZwH6MZVJ52nu7nCuJN0BnFWMtN7mA1ASblLH7zsJvqT6DKqi42_SXLjdi_2xF8o1-3jTasAbslRUgJPcOBH6VdYlmeWLjcxEDpemsA"
    )

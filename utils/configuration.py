#!/usr/bin/env python3
import logging
import inspect
import argparse
import os
from pathlib import Path
import re


from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper



logging.basicConfig(
    level=logging.getLevelName("INFO"),
    format="%(asctime)s %(levelname)-5s %(package)s:%(lineno)d -- %(message)s"
)



class CustomLogRecord(logging.LogRecord):
    def __init__(self, *args, **kwargs):
        super(CustomLogRecord, self).__init__(*args, **kwargs)
        caller = inspect.stack()[5]
        caller_name = caller.frame.f_globals["__name__"]
        self.package = os.path.splitext(self.filename)[0] if caller_name == "__main__" else caller_name



logging.setLogRecordFactory(CustomLogRecord)



class GetAttrRelayer():
    def __init__(self, object, attr):
        self.target_object = object
        self.current_attr = attr

    def __getattr__(self, item):
        return self.target_object.__getattr__(self.current_attr+"_"+item)

    

class ArgFileNone(FileNotFoundError):
    pass



class Configuration(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        self.configuration_dict = dict()
        self.debug = False
        super(Configuration, self).__init__(*args, **kwargs, exit_on_error=False)

    def parse_args(self, args=None, namespace=None):
        self.args = super(Configuration, self).parse_args(args, namespace)
        if self.args.debug:
            self.debug = True
        self.parse_configuration_file()
        self.parse_environment_variables()

        logging.root.setLevel(logging.getLevelName(self.configuration_dict["autop"]["logging"]["level"].upper()))
        self.configuration_dict["autop"]["debug"] = bool(self.configuration_dict["autop"]["debug"])
        return self.configuration_dict

    def parse_configuration_file(self):
        configuration_file_list = [
            self.args.__dict__["config"],
            "/etc/autop.yaml", "/etc/autop.yml",
            os.path.join(Path(__file__).parent.parent, "autop.yaml"),
            os.path.join(Path(__file__).parent.parent, "autop.yml"),
        ]

        for file in configuration_file_list:
            try:
                if file is None:
                    continue
                with open(file, "r") as configuration_file:
                    logging.info("Using configuration file %s" % file)
                    self.configuration_dict = load(configuration_file, Loader=Loader)
                    break
            except FileNotFoundError as e:
                logging.debug("Configuration %s not found, searching next one." % file)
                pass
        if self.configuration_dict["autop"]["debug"]:
            self.debug=True
        if self.debug:
            self.configuration_dict["autop"]["logging"]["level"] = "debug"
            self.configuration_dict["autop"]["debug"] = "True"

    def parse_environment_variables(self):
        def parse_env(configuration_dict):
            target_dict = dict()
            for (k, v) in configuration_dict.items():
                if not isinstance(v, dict):
                    regex_group = re.match('\$\{(?P<env>.+):(?P<DEF>.+)\}', v)
                    if regex_group:
                        target_dict[k] = os.getenv(regex_group.groupdict()["env"], regex_group.groupdict()["DEF"])
                    else:
                        target_dict[k] = v
                if isinstance(v, dict):
                    target_dict[k] = parse_env(v)
            return target_dict
        # print(self.configuration_dict)
        source_dict = self.configuration_dict
        self.configuration_dict.update(**parse_env(source_dict))
        if self.configuration_dict["autop"]["debug"]:
            self.debug=True
        if self.debug:
            self.configuration_dict["autop"]["logging"]["level"] = "debug"
            self.configuration_dict["autop"]["debug"] = True



arguments_parser = Configuration(description='Process some integers.')
arguments_parser.add_argument('--debug',
                    action='store_true',
                    help="Switch debug mode.")
arguments_parser.add_argument('--config -c', dest="config", help="Custom configuration file location.")
configuration = arguments_parser.parse_args()

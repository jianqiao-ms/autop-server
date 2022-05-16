#!/usr/bin/env python3
import re
import uuid
import tortoise.models



class Model(tortoise.models.Model):
    def serialize(self, value):
        if isinstance(value, uuid.UUID):
            return str(value)

        return value

    def dict(self, *args, **kwargs):
        target_fields = args if args else list(filter(lambda x:re.match('[a-zA-Z]', x[0]), self.__dict__.keys()))
        except_fields = kwargs.pop("except", [])

        return dict((x, self.serialize(self.__dict__[x])) for x in filter(lambda x:x not in except_fields, target_fields))

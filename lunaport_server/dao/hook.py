# -*- encoding: utf-8 -*-

"""
    lunaport.dao.hook
    ~~~~~~~~~~~~~~~~~
    One hook entrie for one 3rd party service to to handle hooks from.

"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from sqlalchemy import text, exc
from exceptions import StorageError

from ..wsgi import db
from .. domain.hook import HookBuilder


class Dao(object):
    """Interface for hook_registration  storage"""
    @classmethod
    def get_all(cls):
        raise NotImplemented()


class RDBMS(Dao):
    """PostgreSQL wrapper, implementing hook_registration.dao interface"""

    json_fileds = ['cfg_example']

    @staticmethod
    def rdbms_call(q_text, q_params):
        return db.engine.connect().execute(text(q_text), **q_params)

    @classmethod
    def get_all(cls):
        try:
            rv = cls.rdbms_call('SELECT * from hook', {})
            rows = rv.fetchall()
        except exc.IntegrityError:
            raise StorageError('Some kind of IntegrityError')
        except exc.DataError:
            raise StorageError('One of params malformed or has a wrong type')

        if len(rows) == 0:
            return None

        def create_h(row):
            h_kw = dict(zip(rv.keys(), row))
            return HookBuilder.from_row(**h_kw)

        return map(create_h, rows)

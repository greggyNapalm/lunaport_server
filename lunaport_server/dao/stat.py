# -*- encoding: utf-8 -*-
"""
    lunaport.dao.stat
    ~~~~~~~~~~~~~~~~~
    Storage interaction logic for stat resource.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint
import json

from sqlalchemy import text, exc

from ..wsgi import db
from .. domain.stat import StatBuilder
from exceptions import StorageError


class Stat(object):
    json_fileds = ['doc']

    @staticmethod
    def rdbms_call(q_test, q_params):
        return db.engine.connect().execute(text(q_test), **q_params)

    @classmethod
    def insert(cls, stat):
        kw = stat.as_dict()
        for filed in cls.json_fileds:
            kw.update({filed: json.dumps(kw[filed])})

        def query():
            return cls.rdbms_call('''
INSERT INTO stat
            (test_id,
             ammo_tag,
             version,
             doc)
VALUES
            (:test_id,
             :ammo_tag,
             :version,
             :doc)
RETURNING test_id, ammo_tag''', kw)

        try:
            pk_id = [r for r in query()].pop()[0]
        except exc.IntegrityError as e:
            if 'violates unique constraint "stat_pkey"' in str(e):
                msg = [
                    'stat entrie with such *test_id* and *ammo_tag*',
                    'allready exists.'
                ]
                raise StorageError(' '.join(msg))
            raise StorageError('Some kind of IntegrityError')
        return pk_id

    @classmethod
    def get(cls, test_id, ammo_tag):
        query_params = {
            'test_id': test_id,
            'ammo_tag': ammo_tag,
        }

        rv = cls.rdbms_call('''
SELECT * FROM stat WHERE test_id = :test_id AND ammo_tag = :ammo_tag LIMIT 1;
''', query_params)
        row = rv.first()
        if not row:
            return None

        rv_dict = dict(zip(rv.keys(), row))
        return StatBuilder.from_row(**rv_dict)

    @classmethod
    def avail_ammo_tags(cls, test_id):
        query_params = {
            'test_id': test_id,
        }

        rv = cls.rdbms_call('''
SELECT ammo_tag FROM stat WHERE test_id = :test_id;
''', query_params)
        rows = rv.fetchall()
        if len(rows) == 0:
            return None
        return [row[0] for row in rows]

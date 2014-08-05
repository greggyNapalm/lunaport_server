# -*- encoding: utf-8 -*-
"""
    lunaport.dao.chart
    ~~~~~~~~~~~~~~~~~~
    Storage interaction logic for chart resource.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint
import json

from sqlalchemy import text, exc

from ..wsgi import db
from .. domain.chart import ChartBuilder
from exceptions import StorageError


class Chart(object):
    json_fileds = ['doc']

    @staticmethod
    def rdbms_call(q_test, q_params):
        return db.engine.connect().execute(text(q_test), **q_params)

    @classmethod
    def insert(cls, chart):
        kw = chart.as_dict()
        for filed in cls.json_fileds:
            kw.update({filed: json.dumps(kw[filed])})

        def query():
            return cls.rdbms_call('''
INSERT INTO chart
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
            if 'violates unique constraint "chart_pkey"' in str(e):
                msg = [
                    'chart entrie with such *test_id* and *ammo_tag*',
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
SELECT * FROM chart WHERE test_id = :test_id AND ammo_tag = :ammo_tag LIMIT 1;
''', query_params)
        row = rv.first()
        if not row:
            return None

        rv_dict = dict(zip(rv.keys(), row))
        return ChartBuilder.from_row(**rv_dict)

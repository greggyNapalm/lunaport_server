# -*- encoding: utf-8 -*-
"""
    lunaport.dao.eval
    ~~~~~~~~~~~~~~~~~
    Storage interaction logic for test evaluation resource.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint
import json

from sqlalchemy import text, exc

from ..wsgi import app, db
from .. domain.eval import EvalBuilder
from exceptions import StorageError


class Eval(object):
    json_fileds = ['oracle', 'result']

    per_page_default = app.config.get('EVAL_PER_PAGE_DEFAULT') or 10
    per_page_max = app.config.get('EVAL_PER_PAGE_MAX') or 100

    @staticmethod
    def rdbms_call(q_test, q_params):
        return db.engine.connect().execute(text(q_test), **q_params)

    @classmethod
    def insert(cls, t_eval):
        kw = t_eval.as_dict()
        for filed in cls.json_fileds:
            kw.update({filed: json.dumps(kw[filed])})

        def query():
            return cls.rdbms_call('''
INSERT INTO evaluation
            (test_id,
             oracle,
             result,
             passed)
VALUES
            (:test_id,
             :oracle,
             :result,
             :passed)
RETURNING id''', kw)

        try:
            pk_id = [r for r in query()].pop()[0]
        except exc.IntegrityError:
            raise StorageError('Some kind of IntegrityError')
        return pk_id

    @classmethod
    def get(cls, t_eval_id):
        query_params = {
            't_eval_id': t_eval_id,
        }

        rv = cls.rdbms_call('''
SELECT * FROM evaluation WHERE id = :t_eval_id LIMIT 1;
''', query_params)
        row = rv.first()
        if not row:
            return None

        rv_dict = dict(zip(rv.keys(), row))
        return EvalBuilder.from_row(**rv_dict)

    @classmethod
    def get_many(cls, **kw):
        """pagination"""
        pagination_part = '\nORDER BY id DESC\nLIMIT :limit OFFSET :offset'
        param_per_page = kw.get('per_page')

        if param_per_page and (param_per_page <= cls.per_page_max):
            per_page = param_per_page
        else:
            per_page = cls.per_page_default

        page_num = kw.get('page')
        # page number starts from 1, page 0 and 1 mean the same -
        # first slice from data set.
        if page_num and isinstance(page_num, int) and (page_num >= 2):
            offset = (page_num - 1) * per_page
            next_page = page_num + 1
            prev_page = page_num - 1
        else:
            offset = 0
            next_page = 2
            prev_page = None

        query_params = {
            'limit': per_page,
            'offset': offset,
        }

        """filtering"""
        filter_stmt = []
        if 'test_id' in kw:
            filter_stmt.append('test_id = :test_id')
            query_params.update({'test_id': kw['test_id']})
        if 'passed' in kw:
            filter_stmt.append('passed = :passed')
            query_params.update({'passed': kw['passed']})
        if filter_stmt:
            filter_stmt = 'WHERE {}'.format(',\n'.join(filter_stmt))
        else:
            filter_stmt = ''
        stmt = '''
SELECT * FROM evaluation
{filter}
{pagination}
        '''.format(**{'filter': filter_stmt, 'pagination': pagination_part})
        rv = cls.rdbms_call(stmt, query_params)
        rows = rv.fetchall()

        if len(rows) == 0:
            return None, None, None, None
        elif len(rows) < per_page:  # last chunk of data
            next_page = None

        def create_eval(row):
            e_kw = dict(zip(rv.keys(), row))
            return EvalBuilder.from_row(**e_kw)

        return map(create_eval, rows), per_page, next_page, prev_page

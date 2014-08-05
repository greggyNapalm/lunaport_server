# -*- encoding: utf-8 -*-

"""
    lunaport.dao.case
    ~~~~~~~~~~~~~~~~~
    Storage interaction logic for test case resource.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint
import json

from sqlalchemy import text, exc

from ..wsgi import app, db
from .. domain.case import CaseBuilder
from exceptions import StorageError


class Dao(object):
    """Interface for case storage"""
    @classmethod
    def insert(cls, case):
        raise NotImplemented()

    @classmethod
    def update_by_id(cls, case_id, case_diff):
        raise NotImplemented()

    @classmethod
    def get_by_id(cls, case_id):
        raise NotImplemented()

    @classmethod
    def get_by_name(cls, case_name):
        raise NotImplemented()

    @classmethod
    def get_many(cls, **kw):
        raise NotImplemented()

    @classmethod
    def get_names_butch(cls):
        raise NotImplemented()


class RDBMS(Dao):
    json_fileds = ['oracle', 'notification']
    per_page_default = app.config.get('CASE_PER_PAGE_DEFAULT') or 10
    per_page_max = app.config.get('CASE_PER_PAGE_MAX') or 100

    @staticmethod
    def rdbms_call(q_test, q_params):
        return db.engine.connect().execute(text(q_test), **q_params)

    @classmethod
    def insert(cls, case):
        kw = case.as_dict()
        for filed in cls.json_fileds:
            kw.update({filed: json.dumps(kw[filed])})

        def query():
            return cls.rdbms_call('''
INSERT INTO "case"
            (name,
             descr,
             oracle,
             notification)
VALUES
            (:name,
             :descr,
             :oracle,
             :notification)
RETURNING id''', kw)
        try:
            pk_id = [r for r in query()].pop()[0]
        except exc.IntegrityError as e:
            if 'duplicate key' in str(e) and 'case_name_key' in str(e):
                raise StorageError('*Case* with such uniq name allready exists:{}'.format(
                                   kw.get('name')))
            raise StorageError('Some kind of IntegrityError')
        return pk_id

    @classmethod
    def cmpl_update_sql(cls, case_diff):
        rv = []
        attr_allowed = [
            'name',
            'descr',
            'oracle',
            'notification',
            'root_test_id',
            'etalon_test_id'
        ]
        for attr in attr_allowed:
            if attr in case_diff.keys():
                rv.append('{} = :{}'.format(attr, attr))
        rv.append('changed_at = NOW()')
        return ',\n'.join(rv)

    @classmethod
    def update_by_id(cls, case_id, case_diff):
        for filed in cls.json_fileds:
            if (filed in case_diff.keys()) and \
                    (not isinstance(case_diff[filed], basestring)):
                case_diff.update({filed: json.dumps(case_diff[filed])})

        def query():
            q_params = case_diff
            q_params.update({
                'case_id': case_id,
            })
            top = '''UPDATE "case"
SET
'''
            bottom = '''
WHERE  id = :case_id
RETURNING id'''
            update = cls.cmpl_update_sql(case_diff)
            return cls.rdbms_call(''.join([top, update, bottom]), q_params)

        try:
            pk_id = [r for r in query()].pop()[0]
        except exc.IntegrityError as e:
            if 'violates foreign key constraint "case_root_test_id_fkey"' in str(e):
                raise StorageError(
                    'unknown *root_test_id* value:{}'.format(case_diff.get('root_test_id')))

            raise StorageError('Some kind of IntegrityError')
        return cls.get_by_id(pk_id)

    @classmethod
    def get_by_id(cls, case_id):
        query_params = {
            'case_id': case_id,
        }

        rv = cls.rdbms_call('''
SELECT * FROM "case" WHERE id = :case_id LIMIT 1;
''', query_params)
        row = rv.first()
        if not row:
            return None

        rv_dict = dict(zip(rv.keys(), row))
        return CaseBuilder.from_row(**rv_dict)

    @classmethod
    def get_by_name(cls, case_name):
        query_params = {
            'case_name': case_name,
        }

        rv = cls.rdbms_call('''
SELECT * FROM "case" WHERE name = :case_name LIMIT 1;
''', query_params)
        row = rv.first()
        if not row:
            return None

        rv_dict = dict(zip(rv.keys(), row))
        return CaseBuilder.from_row(**rv_dict)

    @classmethod
    def get_many(cls, **kw):
        """pagination"""
        pagination_part = '\nLIMIT :limit OFFSET :offset'
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

        top = """
SELECT * from "case" WHERE id != 1
"""
        order_part = 'ORDER BY id DESC'
        rv = cls.rdbms_call(
            ''.join([top, order_part, pagination_part,]),
            query_params)

        rows = rv.fetchall()
        if len(rows) == 0:
            return None, None, None, None

        elif len(rows) < per_page:  # last chunk of data
            next_page = None

        def create_case(row):
            t_kw = dict(zip(rv.keys(), row))
            return CaseBuilder.from_row(**t_kw)

        return map(create_case, rows), per_page, next_page, prev_page

    @classmethod
    def get_names_butch(cls):
        rv = cls.rdbms_call(
            'select id, name from "case" order by name', {})
        #return [el[0] for el in rv.fetchall()]
        return [list(el) for el in rv.fetchall()]

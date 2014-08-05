# -*- encoding: utf-8 -*-

"""
    lunaport.dao.dc
    ~~~~~~~~~~~~~~~
    Storage interaction logic for dc resource.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from sqlalchemy import text, exc

from ..wsgi import app, db
from .. domain.dc import DcBuilder, DcAdaptor
from exceptions import StorageError


class Filter(object):
    params_allowed = {
        'name': (
            "AND name LIKE '%:name%'"),
    }
    cast_to_int = []

    def __init__(self, **kw):
        self.rule = []
        self.q_params = {}
        for p, v in kw.iteritems():
            if p not in self.params_allowed.keys():
                continue
            elif isinstance(v, (unicode, basestring)):
                self.rule.append(self.params_allowed[p][0])
                self.q_params.update({p: v})
            else:
                raise StorageError('Wrong *{}* param type.'.format(p))

    def cmpl_query(self):
        sql_text = '\n' + ' '.join(self.rule)
        return sql_text, self.q_params


class Dao(object):
    """Interface for dc storage"""
    @classmethod
    def insert(cls, ammo):
        raise NotImplemented()

    @classmethod
    def get_single(cls, **kw):
        raise NotImplemented()

    @classmethod
    def get_many(cls, **kw):
        raise NotImplemented()


class RDBMS(Dao):
    """PostgreSQL wrapper, implementing dc.dao interface"""
    per_page_default = app.config.get('DC_PER_PAGE_DEFAULT') or 10
    per_page_max = app.config.get('DC_PER_PAGE_MAX') or 100
    select_join_part = '''
SELECT a.*,
       c.name        AS case,
       c.id          AS case_id,
       own.login AS owner
FROM   ammo a,
       "case" c,
       "user" own
WHERE a.case_id = c.id
        AND a.owner_id = own.id'''
    select_part = '''
SELECT * from dc'''

    @staticmethod
    def rdbms_call(q_text, q_params):
        return db.engine.connect().execute(text(q_text), **q_params)

    @classmethod
    def insert(cls, dc):
        kw = DcAdaptor.to_dict(dc)

        def query():
            return cls.rdbms_call('''
INSERT INTO dc (name) VALUES (:name)
returning id''', kw)
        err_duplicate = 'datacenter:{} allready exists'.format(kw.get('name'))
        try:
            pk_id = [r for r in query()].pop()[0]
        except IndexError:
            raise StorageError(err_duplicate)
        except exc.IntegrityError as e:
            if 'unique constraint "dc_name_key"' in str(e):
                raise StorageError(err_duplicate)
            raise StorageError('Some kind of IntegrityError')
        return pk_id

    @classmethod
    def get_single(cls, **kw):
        if kw.get('name'):
            query_params = {
                'name': kw.get('name'),
            }
            condition_part = 'WHERE name = :name'
        if kw.get('dc_id'):
            query_params = {
                'dc_id': kw.get('dc_id'),
            }
            condition_part = 'WHERE id = :dc_id'

        rv = cls.rdbms_call(' '.join([cls.select_part, condition_part]), query_params)
        row = rv.first()
        if not row:
            return None

        t_kw = dict(zip(rv.keys(), row))
        return DcBuilder.from_row(**t_kw)

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
        f = Filter(**kw)
        filter_part, q_params_up = f.cmpl_query()
        query_params.update(q_params_up)

        rv = cls.rdbms_call(
            ''.join([cls.select_part, filter_part, pagination_part]),
            query_params)

        rows = rv.fetchall()
        if len(rows) == 0:
            return None, None, None, None
        elif len(rows) < per_page:  # last chunk of data
            next_page = None

        def create_dc(row):
            t_kw = dict(zip(rv.keys(), row))
            return DcBuilder.from_row(**t_kw)

        return map(create_dc, rows), per_page, next_page, prev_page

    @classmethod
    def update_or_create(cls, dc_entrie):
        q_params = DcAdaptor.to_dict(dc_entrie)
        condition_part = '''
INSERT INTO dc (name) SELECT :name
WHERE NOT EXISTS (SELECT 1 FROM dc WHERE name=:name)
'''
        rv = cls.rdbms_call(condition_part + ' RETURNING id', q_params)
        row = rv.first()
        if not row:
            return cls.get_single(name=dc_entrie.name)

        return cls.get_single(dc_id=row[0])

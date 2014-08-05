# -*- encoding: utf-8 -*-

"""
    lunaport.dao.line
    ~~~~~~~~~~~~~~~~~
    Storage interaction logic for line resource.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from sqlalchemy import text, exc

from ..wsgi import app, db
from .. domain.line import LineBuilder, LineAdaptor
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
    """Interface for line storage"""
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
    """PostgreSQL wrapper, implementing line.dao interface"""

    per_page_default = app.config.get('LINE_PER_PAGE_DEFAULT') or 10
    per_page_max = app.config.get('LINE_PER_PAGE_MAX') or 100
    select_join_part = '''
SELECT l.*,
       dc.name        AS dc_name
FROM   line l,
       dc dc
WHERE l.dc_id = dc.id'''

    @staticmethod
    def rdbms_call(q_text, q_params):
        return db.engine.connect().execute(text(q_text), **q_params)

    @classmethod
    def insert(cls, line):
        kw = LineAdaptor.to_dict(line)
        kw['dc_name'] = kw['dc']['name']
        pp(kw)

        def query():
            return cls.rdbms_call('''
INSERT INTO line
            (
             id,
             name,
             dc_id
            )
VALUES      (
             :id,
             :name,
             (SELECT id FROM dc WHERE  name = :dc_name)
            )
returning id''', kw)
        err_duplicate = 'line:{} allready exists'.format(kw.get('name'))
        try:
            pk_id = [r for r in query()].pop()[0]
        except exc.IntegrityError as e:
            if 'unique constraint "line_pkey"' in str(e):
                raise StorageError(err_duplicate)
            raise StorageError('Some kind of IntegrityError')
        return pk_id

    @classmethod
    def get_single(cls, **kw):
        if kw.get('line_id'):
            query_params = {
                'line_id': kw.get('line_id'),
            }
        rv = cls.rdbms_call(' '.join([cls.select_join_part, 'AND l.id = :line_id']), query_params)
        row = rv.first()
        if not row:
            return None

        t_kw = dict(zip(rv.keys(), row))
        return LineBuilder.from_row(**t_kw)

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
            ''.join([cls.select_join_part, filter_part, pagination_part]),
            query_params)

        rows = rv.fetchall()
        if len(rows) == 0:
            return None, None, None, None
        elif len(rows) < per_page:  # last chunk of data
            next_page = None

        def create_dc(row):
            t_kw = dict(zip(rv.keys(), row))
            return LineBuilder.from_row(**t_kw)

        return map(create_dc, rows), per_page, next_page, prev_page

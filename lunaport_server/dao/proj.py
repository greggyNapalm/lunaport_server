# -*- encoding: utf-8 -*-

"""
    lunaport.dao.proj
    ~~~~~~~~~~~~~~~~~
    Storage interaction logic for project(proj) resource.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4)

from sqlalchemy import text, exc

from ..wsgi import app, db
from .. domain.proj import ProjBuilder
from exceptions import StorageError


class Filter(object):
    params_allowed = {
        'title': (
            'AND i.title ~ :title',
            'AND i.title ~ ANY (:title)'),
        'descr': (
            'AND i.descr ~ :descr',
            'AND i.descr ~ ANY (:descr)'),
        'reporter': (
            'AND r.login = :reporter',
            'AND r.login = ANY (:reporter)'),
        'assignee': (
            'AND a.login = :assignee',
            'AND a.login = ANY (:assignee)'),
    }
    cast_to_int = []

    def __init__(self, **kw):
        self.rule = []
        self.q_params = {}
        for p, v in kw.iteritems():
            if p not in self.params_allowed.keys():
                continue
            if isinstance(v, (list, tuple)):
                if p in self.cast_to_int:  # autocast doesn't work for ARRAY
                    v = [int(el) for el in v]
                self.rule.append(self.params_allowed[p][1])
                self.q_params.update({p: v})
            elif isinstance(v, (unicode, basestring)):
                self.rule.append(self.params_allowed[p][0])
                self.q_params.update({p: v})
            else:
                raise StorageError('Wrong *{}* param type.'.format(p))

    def cmpl_query(self):

        sql_text = '\n' + ' '.join(self.rule)
        return sql_text, self.q_params


class Dao(object):
    """Interface for proj storage"""
    @classmethod
    def insert(cls, case):
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


class RDBMS(object):
    json_fileds = ['added_at']
    per_page_default = app.config.get('PROJ_PER_PAGE_DEFAULT') or 10
    per_page_max = app.config.get('PROJ_PER_PAGE_MAX') or 100
    select_join_part = '''
SELECT  i.*,
        r.login AS reporter_login,
        a.login AS assignee_login
FROM    issue i,
        "user" r,
        "user" a
WHERE   i.id != 1
        AND i.reporter = r.id
        AND  i.assignee = a.id'''

    @staticmethod
    def rdbms_call(q_stmt, q_params):
        return db.engine.connect().execute(text(q_stmt), **q_params)

    @classmethod
    def insert(cls, proj):
        q_params = proj.as_dict()

        def query():
            return cls.rdbms_call('''
INSERT INTO project
            (name,
             descr,
             provider,
             lead
)
VALUES      (:name,
             :descr,
             :provider,
             :lead
)
RETURNING id''', q_params)
        try:
            pk_id = [r for r in query()].pop()[0]
        except exc.IntegrityError as e:
            dupl_err = 'proj with name *{}* allready exists'
            if 'duplicate key' in str(e) and 'project_name_key' in str(e):
                raise StorageError(
                    dupl_err.format(q_params.get('name')))
            raise StorageError('Some kind of IntegrityError')
        return pk_id

    @classmethod
    def get_by_name(cls, **kw):
        query_params = {
            'name': kw.get('proj_name'),
        }

        stmt = """
SELECT * from "project" WHERE name = :name
"""

        rv = cls.rdbms_call(stmt, query_params)
        row = rv.first()
        if not row:
            return None

        p_kw = dict(zip(rv.keys(), row))
        return ProjBuilder.from_row(**p_kw)

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
        else:
            offset = 0
            next_page = 2

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
            return None, None, None

        def create_proj(row):
            t_kw = dict(zip(rv.keys(), row))
            return ProjBuilder.from_row(**t_kw)

        return map(create_proj, rows), per_page, next_page

    @classmethod
    def get_names_butch(cls):
        rv = cls.rdbms_call(
            'select name from project order by name', {})
        return [el[0] for el in rv.fetchall()]

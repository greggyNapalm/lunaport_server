# -*- encoding: utf-8 -*-

"""
    lunaport.dao.hook_registration
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    hook_registration - m2m connection case with hook. Rule to starte test.

"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from sqlalchemy import text, exc
from exceptions import StorageError

from ..wsgi import app, db
from .. domain.hook_registration import HookRegistrationBuilder, HookRegistrationAdaptor


class Filter(object):
    params_allowed = {
        'case_name': (
            'AND c.name = :case_name',
            'AND c.name = ANY (:case_name)'),
        'case_id': (
            'AND c.id = :case_id',
            'AND c.id = ANY (:case_id)'),
        'hook_name': (
            'AND h.name = :hook_name',
            'AND hook_name = ANY (:hook_name)'),
        'is_enabled': (
            'AND r.is_enabled = :is_enabled',
            ''),
        'owner': (
            'AND owner.login = :owner',
            'AND owner.login = ANY (:owner)'),
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
    """Interface for hook_registration  storage"""
    @classmethod
    def insert(cls, h_rg):
        raise NotImplemented()

    @classmethod
    def update_by_id(cls, h_rg_id, h_rg_diff):
        raise NotImplemented()

    @classmethod
    def get_single(cls, **kw):
        raise NotImplemented()

    @classmethod
    def get_many(cls, **kw):
        raise NotImplemented()


class RDBMS(Dao):
    """PostgreSQL wrapper, implementing hook_registration.dao interface"""

    json_fileds = ['cfg']
    dt_fileds = ['added_at', 'last_used_at']
    per_page_default = app.config.get('HOOKS_REG_PER_PAGE_DEFAULT') or 10
    per_page_max = app.config.get('HOOKS_REG_PER_PAGE_MAX') or 100
    select_join_part = '''
SELECT r.*,
       c.name        AS case,
       c.id          AS case_id,
       h.name        AS hook_name,
       own.login AS owner
FROM   hook_registration r,
       "case" c,
       "user" own,
       hook h
WHERE r.case_id = c.id
        AND r.owner_id = own.id
        AND r.hook_id = h.id'''

    @staticmethod
    def rdbms_call(q_text, q_params):
        return db.engine.connect().execute(text(q_text), **q_params)

    @classmethod
    def insert(cls, h_reg):
        kw = HookRegistrationAdaptor.to_dict(h_reg)
        for filed in cls.json_fileds:
            kw.update({filed: json.dumps(kw[filed])})

        def query():
            return cls.rdbms_call('''
INSERT INTO hook_registration
            (case_id,
             hook_id,
             descr,
             owner_id,
             is_enabled,
             cfg)
VALUES      (
              :case_id,
              :hook_id,
              :descr,
              (SELECT id FROM "user" WHERE  login = :owner),
              :is_enabled,
              :cfg) returning id''', kw)
        try:
            pk_id = [r for r in query()].pop()[0]
        except exc.IntegrityError as e:
            raise StorageError('Some kind of IntegrityError')
        return pk_id

    @classmethod
    def update_by_id(cls, h_rg_id, h_rg_diff):
        def query():
            q_params = h_rg_diff
            q_params.update({
                'h_rg_id': h_rg_id,
            })
            set_stmt = []
            if q_params.get('cfg'):
                q_params['cfg'] = json.dumps(q_params['cfg'])
                set_stmt.append('cfg = :cfg')

            if q_params.get('is_enabled'):
                set_stmt.append('is_enabled = :is_enabled')

            q_stmt = '''
UPDATE "hook_registration"
SET {}
WHERE id = :h_rg_id
RETURNING id'''.format(',\n'.join(set_stmt))
            if not set_stmt:  # nothing to update
                raise AssertionError('Nothing to update')
            return cls.rdbms_call(q_stmt, q_params)

        try:
            [r for r in query()].pop()[0]
        except exc.IntegrityError as e:
            raise StorageError('Some kind of IntegrityError')
        except IndexError:
                raise StorageError(
                    'no such hook_registration with id:{}'.format(h_rg_diff['h_rg_id']))
        return cls.get_single(hook_registration_id=h_rg_id)

    @classmethod
    def get_single(cls, **kw):
        filter_part = ''
        if kw.get('hook_registration_id'):
            query_params = {
                'hook_registration_id': kw.get('hook_registration_id'),
            }
            filter_part = '\nAND r.id = :hook_registration_id'
        rv = cls.rdbms_call(''.join([cls.select_join_part, filter_part]),
                            query_params)
        row = rv.first()
        if not row:
            return None

        t_kw = dict(zip(rv.keys(), row))
        return HookRegistrationBuilder.from_row(**t_kw)

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

        def create_hr(row):
            hr_kw = dict(zip(rv.keys(), row))
            return HookRegistrationBuilder.from_row(**hr_kw)

        return map(create_hr, rows), per_page, next_page, prev_page

    @classmethod
    def delete(cls, h_reg_id):
        query_stmt = '''
DELETE FROM hook_registration WHERE
    id = :h_reg_id
RETURNING id'''
        try:
            rv = cls.rdbms_call(query_stmt, {'h_reg_id': h_reg_id})
        except exc.IntegrityError:
            raise StorageError('Some kind of IntegrityError')

        if len(rv.fetchall()) < 1:
            raise ValueError('Inconsistent query param hook_registration id')
        return True

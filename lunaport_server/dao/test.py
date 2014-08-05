# -*- encoding: utf-8 -*-

"""
    lunaport.dao.test
    ~~~~~~~~~~~~~~~~~
    Storage interaction logic for test resource.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint
import json

import redis
import dateutil.parser
from sqlalchemy import text, exc
from lunaport_worker.tasks.check import reduce_arts

from ..wsgi import app, db
from .. domain.test import TestBuilder
from exceptions import StorageError


class Filter(object):
    params_allowed = {
        'case': (
            'AND c.name = :case',
            'AND c.name = ANY (:case)'),
        'owner': (
            'AND owner.login = :owner',
            'AND owner.login = ANY (:owner)'),
        'issue': (
            'AND issue.name = :issue',
            'AND issue.name = ANY (:issue)'),
        'load_src': (
            'AND load_src.fqdn = :load_src',
            'AND load_src.fqdn = ANY (:load_src)'),
        'load_dst': (
            'AND load_dst.fqdn = :load_dst',
            'AND load_dst.fqdn = ANY (:load_dst)'),
        'parent': (
            'AND t.parent_id = :parent',
            'AND t.parent_id = ANY (:parent)'),
        'ammo': (
            'AND t.ammo_id = :ammo',
            'AND t.ammo_id = ANY (:ammo)'),
        'status': (
            'AND s.name = :status',
            'AND s.name = ANY (:status)'),
    }
    cast_to_int = ['parent']

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
    """Interface for test storage"""
    @classmethod
    def insert(cls, test):
        raise NotImplemented()

    @classmethod
    def update_by_id(cls, test_id, test_diff):
        raise NotImplemented()

    @classmethod
    def get_by_id(cls, **kw):
        raise NotImplemented()

    @classmethod
    def get_many(cls, **kw):
        raise NotImplemented()


class RDBMS(Dao):
    """PostgreSQL wrapper, implementing test.dao interface"""

    json_fileds = ['lll', 'files', 'generator_cfg']
    dt_fileds = ['added_at', 'started_at', 'finished_at']
    per_page_default = app.config.get('TEST_PER_PAGE_DEFAULT') or 10
    per_page_max = app.config.get('TEST_PER_PAGE_MAX') or 100
    select_join_part = '''
SELECT t.*,
       s.name        AS status,
       c.name        AS case,
       c.id          AS case_id,
       eng.name      AS engine,
       env.name      AS env,
       inic.login AS initiator,
       issue.name    AS issue,
       load_src.fqdn AS load_src,
       load_dst.fqdn AS load_dst
FROM   test t,
       t_status s,
       "case" c,
       engine eng,
       environment env,
       "user" inic,
       issue,
       server load_src,
       server load_dst
WHERE  t.case_id = c.id
       AND t.t_status_id = s.id
       AND t.engine_id = eng.id
       AND t.environment_id = env.id
       AND t.initiator_id = inic.id
       AND t.issue_id = issue.id
       AND t.load_src_id = load_src.id
       AND t.load_dst_id = load_dst.id'''

    @staticmethod
    def rdbms_call(q_test, q_params):
        return db.engine.connect().execute(text(q_test), **q_params)

    @classmethod
    def insert(cls, test):
        kw = test.as_dict(cuted=False)
        for filed in cls.json_fileds:
            kw.update({filed: json.dumps(kw[filed])})

        def query(parent_test_id):
            parent_str = \
                '(SELECT root_test_id FROM "case" WHERE  name = :case),'
            if parent_test_id and isinstance(parent_test_id, int):
                parent_str = '(SELECT {}),'.format(parent_test_id)
            return cls.rdbms_call('''
INSERT INTO test
            (t_status_id,
             case_id,
             ammo_id,
             parent_id,
             engine_id,
             environment_id,
             lll_id,
             lll,
             initiator_id,
             "name",
             descr,
             issue_id,
             load_src_id,
             load_dst_id,
             started_at,
             finished_at,
             files,
             generator_cfg)
VALUES      ( (SELECT id FROM t_status WHERE  name = :status),
              (SELECT id FROM "case" WHERE  name = :case),
              (SELECT id FROM "ammo" WHERE  path = :ammo_path),
              ''' + parent_str + '''
              (SELECT id FROM engine WHERE name = :engine),
              (SELECT id FROM environment WHERE name = :env),
              :lll_id,
              :lll,
              (SELECT id FROM "user" WHERE  login = :initiator),
              :name,
              :descr,
              (SELECT id FROM "issue" WHERE name = :issue),
              (SELECT id FROM server WHERE  fqdn = :load_src),
              (SELECT id FROM server WHERE  fqdn = :load_dst),
              :started_at,
              :finished_at,
              :files,
              :generator_cfg) returning id''', kw)
        try:
            pk_id = [r for r in query(kw.get('parent_id'))].pop()[0]
        except exc.IntegrityError as e:
            if 'null value in column "initiator_id"' in str(e):
                raise StorageError(
                    'unknown *initiator* value:{}'.format(kw.get('initiator')),
                    missing_resource_type='user',
                    missing_resource_value=kw.get('initiator'),)
            if 'null value in column "case_id"' in str(e):
                raise StorageError(
                    'unknown *case* value:{}'.format(kw.get('case')),
                    missing_resource_type='case',
                    missing_resource_value=kw.get('case'),)
            if 'null value in column "issue_id"' in str(e):
                raise StorageError(
                    'unknown *issue* value:{}'.format(kw.get('issue')),
                    missing_resource_type='issue',
                    missing_resource_value=kw.get('issue'),)
            if 'null value in column "load_src_id"' in str(e):
                raise StorageError(
                    'unknown *load_src* value:{}'.format(kw.get('load_src')),
                    missing_resource_type='host',
                    missing_resource_value=kw.get('load_src'),)
            if 'null value in column "load_dst_id"' in str(e):
                raise StorageError(
                    'unknown *load_dst* value:{}'.format(kw.get('load_dst')),
                    missing_resource_type='host',
                    missing_resource_value=kw.get('load_dst'),)
            raise StorageError('Some kind of IntegrityError')
        return pk_id

    @classmethod
    def update_by_id(cls, test_id, test_diff):
        def query():
            q_params = test_diff
            q_params.update({
                'test_id': test_id,
            })
            set_stmt = []
            if q_params.get('status'):
                set_stmt.append(
                    't_status_id=(SELECT id FROM t_status WHERE name = :status)')

            if 'finished_at' in q_params:
                set_stmt.append('finished_at = :finished_at')
                q_params['finished_at'] = dateutil.parser.parse(
                    q_params['finished_at'])

            if 'started_at' in q_params:
                set_stmt.append('started_at = :started_at')
                q_params['started_at'] = dateutil.parser.parse(
                    q_params['started_at'])

            if 'resolution' in q_params:
                set_stmt.append('resolution = :resolution')

            if 'lll' in q_params:
                if q_params['lll'].get('n'):
                    q_params['lll_id'] = q_params['lunapark']['n']
                    set_stmt.append('lll_id = :lunapark_id')

                q_params['lll'] = json.dumps(q_params['lunapark'])
                set_stmt.append('lll = :lunapark')

            q_stmt = '''
UPDATE "test"
SET {}
WHERE id = :test_id
RETURNING id'''.format(',\n'.join(set_stmt))
            if not set_stmt:  # nothing to update
                raise AssertionError('Nothing to update')
            return cls.rdbms_call(q_stmt, q_params)

        try:
            #pk_id = [r for r in query()].pop()[0]
            query()
        except exc.IntegrityError as e:
            if 'null value in column "t_status_id"' in str(e):
                raise StorageError(
                    "unknown *status* value:{}".format(test_diff['status']))
            raise StorageError('Some kind of IntegrityError')
        except IndexError:
                raise StorageError(
                    'no such test with id:{}'.format(test_diff['test_id']))
        return cls.get_by_id(test_id=test_id)

    @classmethod
    def get_by_id(cls, **kw):
        if kw.get('test_id'):
            query_params = {
                'test_id': kw.get('test_id'),
            }
            filter_part = '\nAND t.id = :test_id'
        elif kw.get('lll_id'):
            query_params = {
                'lll_id': kw.get('lunapark_id'),
            }
            filter_part = '\nAND t.lll_id = :lunapark_id'

        rv = cls.rdbms_call(''.join([cls.select_join_part, filter_part]),
                            query_params)
        row = rv.first()
        if not row:
            return None

        t_kw = dict(zip(rv.keys(), row))
        return TestBuilder.from_row(**t_kw)

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

        try:
            rv = cls.rdbms_call(
                ''.join([cls.select_join_part, filter_part, pagination_part]),
                query_params)
            rows = rv.fetchall()
        except exc.IntegrityError:
            raise StorageError('Some kind of IntegrityError')
        except exc.DataError:
            raise StorageError('One of params malformed or has a wrong type')

        if len(rows) == 0:
            return None, None, None, None
        elif len(rows) < per_page:  # last chunk of data
            next_page = None

        def create_test(row):
            t_kw = dict(zip(rv.keys(), row))
            return TestBuilder.from_row(**t_kw)

        return map(create_test, rows), per_page, next_page, prev_page


class SideEffect(Dao):
    """Side effect wrapper, implementing test.dao interface.
    """
    def __init__(self, dao):
        self.dao = dao
        self.redis = redis.Redis(**app.config.get('REDIS_CLIENT'))
        self.rds_monitor_finish = 'lll_monitor_finish'
        self.rds_monitor_start = 'lll_monitor_start'

    def insert(self, test):
        test.id = self.dao.insert(test)
        if test.env in ['luna-tank-api', 'luna-tank-api-force'] and\
                test.status != 'finished':
            self.schedule_to_monitor_finish(test)

        if test.env == 'luna-tank-api-force':
            self.schedule_to_monitor_start(test)
        elif test.env == 'yandex-tank':
            reduce_arts.apply_async(args=[test.id, test.files])
        return test.id

    def update_by_id(self, test_id, test_diff):
        return self.dao.update_by_id(test_id, test_diff)

    def get_by_id(self, **kw):
        return self.dao.get_by_id(**kw)

    def get_many(self, **kw):
        return self.dao.get_many(**kw)

    def schedule_to_monitor(self, key, test):
        """ Put test data to Redis hash whith running lll tests.
            This hash periodically pulled by Celery workers which
            fires reduce jobs on just finished tests.
        """
        self.redis.hset(key, test.id, test.to_monitor_dct())

    def schedule_to_monitor_finish(self, test):
        self.schedule_to_monitor(self.rds_monitor_finish, test)

    def schedule_to_monitor_start(self, test):
        self.schedule_to_monitor(self.rds_monitor_start, test)

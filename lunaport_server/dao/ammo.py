# -*- encoding: utf-8 -*-

"""
    lunaport.dao.ammo
    ~~~~~~~~~~~~~~~~~
    Storage interaction logic for ammo resource.
"""

import os
import hashlib
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint
import json
import datetime as dt

from sqlalchemy import text, exc

from ..wsgi import app, db
from .. domain.ammo import AmmoBuilder, AmmoAdaptor
from exceptions import StorageError


class Filter(object):
    params_allowed = {
        'case': (
            'AND c.name = :case',
            'AND c.name = ANY (:case)'),
        'owner': (
            'AND own.login = :owner',
            'AND own.login = ANY (:owner)'),
        'hash': (
            'AND a.hash = :hash',
            'AND a.hash = ANY (:hash)'),
        'path': (
            'AND a.path = :path',
            'AND a.path = ANY (:path)'),
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
    """Interface for ammo storage"""
    @classmethod
    def save_file(cls, ammo):
        raise NotImplemented()

    @classmethod
    def insert(cls, ammo):
        raise NotImplemented()

    @classmethod
    def update_by_id(cls, ammo_id, ammo_diff):
        raise NotImplemented()

    @classmethod
    def get_single(cls, **kw):
        raise NotImplemented()

    @classmethod
    def get_many(cls, **kw):
        raise NotImplemented()


class RDBMS(Dao):
    """PostgreSQL wrapper, implementing ammo.dao interface"""

    json_fileds = ['meta']
    dt_fileds = ['added_at', 'last_used_at']
    per_page_default = app.config.get('AMMO_PER_PAGE_DEFAULT') or 10
    per_page_max = app.config.get('AMMO_PER_PAGE_MAX') or 100
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

    @staticmethod
    def rdbms_call(q_text, q_params):
        return db.engine.connect().execute(text(q_text), **q_params)

    @classmethod
    def insert(cls, ammo, md5, sha256, size):
        kw = {
            'ammo_hash': '{}|{}|{}'.format(md5, size, sha256)
        }
        kw.update(AmmoAdaptor.to_dict(ammo))
        for filed in cls.json_fileds:
            kw.update({filed: json.dumps(kw[filed])})

        def query():
            return cls.rdbms_call('''
INSERT INTO ammo
            (case_id,
             owner_id,
             name,
             descr,
             hash)
VALUES      (
              (SELECT id FROM "case" WHERE  name = :case),
              (SELECT id FROM "user" WHERE  login = :owner),
              :name,
              :descr,
              :ammo_hash) returning id''', kw)
        try:
            pk_id = [r for r in query()].pop()[0]
        except exc.IntegrityError as e:
            if 'violates unique constraint "ammo_hash_key"' in str(e):
                raise ValueError(
                    'ammo file exists, hash: {}'.format(kw.get('ammo_hash')))
            if 'null value in column "case_id"' in str(e):
                raise StorageError(
                    'unknown *case* value:{}'.format(kw.get('case')),
                    missing_resource_type='case',
                    missing_resource_value=kw.get('case'),)

            raise StorageError('Some kind of IntegrityError')
        return pk_id

    @classmethod
    def update_by_id(cls, ammo_id, ammo_diff):
        def query():
            q_params = ammo_diff
            q_params.update({
                'ammo_id': ammo_id,
            })
            set_stmt = []
            if q_params.get('path'):
                set_stmt.append('path = :path')
            q_stmt = '''
UPDATE "ammo"
SET {}
WHERE id = :ammo_id
RETURNING id'''.format(',\n'.join(set_stmt))
            if not set_stmt:  # nothing to update
                raise AssertionError('Nothing to update')
            return cls.rdbms_call(q_stmt, q_params)

        try:
            [r for r in query()].pop()[0]
        except exc.IntegrityError as e:
            if 'null value in column "t_status_id"' in str(e):
                raise StorageError(
                    "unknown *status* value:{}".format(ammo_diff['status']))
            raise StorageError('Some kind of IntegrityError')
        except IndexError:
                raise StorageError(
                    'no such test with id:{}'.format(ammo_diff['test_id']))
        return cls.get_single(ammo_id=ammo_id)

    @classmethod
    def get_single(cls, **kw):
        filter_part = ''
        if kw.get('ammo_id'):
            query_params = {
                'ammo_id': kw.get('ammo_id'),
            }
            filter_part = '\nAND a.id = :ammo_id'
        rv = cls.rdbms_call(''.join([cls.select_join_part, filter_part]),
                            query_params)
        row = rv.first()
        if not row:
            return None

        t_kw = dict(zip(rv.keys(), row))
        return AmmoBuilder.from_row(**t_kw)

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

        def create_test(row):
            t_kw = dict(zip(rv.keys(), row))
            return AmmoBuilder.from_row(**t_kw)

        return map(create_test, rows), per_page, next_page, prev_page


class SideEffect(Dao):
    """Side effect wrapper, implementing test.dao interface.
    """
    def __init__(self, dao):
        self.dao = dao
        self.ammo_tmp_path = app.config.get('AMMO_TMP_PATH')
        self.ammo_path = app.config.get('AMMO_PATH')
        for p in [self.ammo_tmp_path, self.ammo_path]:
            if not os.path.exists(p):
                os.makedirs(p)

    def insert(self, ammo):
        ''' Two phase commit system to avoid race condition and malformed data:
            1) Save attached file as tmp
            2) Insert new Ammo entrie to PostgreSQL.
            3) Move tmp file to persistent place.
            4) UPDATE PostgreSQL entrie path attribute.

            NULL path attribute == file not moved yet.
        '''
        tmp_path, persistent_path = self.compose_path(ammo)
        ammo.file_storage.save(tmp_path)

        with open(tmp_path, 'rb') as fh:
            md5, sha256, size_bytes = self.gen_hashes(fh)

        ammo_id = self.dao.insert(ammo, md5, sha256, size_bytes)
        self.move_ammo(tmp_path, persistent_path)

        self.update_by_id(ammo_id, {'path': persistent_path})
        return ammo_id

    def gen_hashes(self, fh):
        md5 = hashlib.md5()
        sha = hashlib.sha256()
        size_bytes = 0
        for chunk in iter(lambda: fh.read(md5.block_size), b''):
            md5.update(chunk)
            sha.update(chunk)
            size_bytes += len(chunk)

        return md5.hexdigest(), sha.hexdigest(), size_bytes

    def update_by_id(self, ammo_id, ammo_diff):
        return self.dao.update_by_id(ammo_id, ammo_diff)

    def get_single(self, **kw):
        return self.dao.get_single(**kw)

    def get_many(self, **kw):
        return self.dao.get_many(**kw)

    def compose_path(self, ammo):
        now = dt.datetime.now()
        day_stamp = now.strftime('%Y%m%d')
        usec_stamp = now.strftime('%s-%f')
        return (
            '{}/{}'.format(self.ammo_tmp_path, now.strftime('%s.%f')),
            '{}/{}/{}/{}_{}'.format(self.ammo_path, ammo.case, day_stamp,
                                    usec_stamp, ammo.file_storage.filename)
        )

    def move_ammo(self, tmp_path, persistent_path):
        try:
            os.makedirs(persistent_path.rsplit('/', 1)[0])
        except OSError as e:
            if e.errno != 17:  # Folder exists
                raise

        os.rename(tmp_path, persistent_path)

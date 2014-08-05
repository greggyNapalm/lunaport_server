# -*- encoding: utf-8 -*-

"""
    lunaport.dao.notification
    ~~~~~~~~~~~~~~~~~~~~~~~~~
    Storage interaction logic for notification resource.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint
import json

from sqlalchemy import text, exc

from ..wsgi import app, db
from .. domain.notification import NotifcnBuilder, NotifcnAdaptor
from exceptions import StorageError


class Notifcn(object):
    json_fileds = ['cfg', ]
    per_page_default = app.config.get('NOTIFICATION_PER_PAGE_DEFAULT') or 10
    per_page_max = app.config.get('NOTIFICATION_PER_PAGE_MAX') or 100

    @staticmethod
    def rdbms_call(q_test, q_params):
        return db.engine.connect().execute(text(q_test), **q_params)

    @classmethod
    def insert(cls, notifcn):
        kw = NotifcnAdaptor.to_dict(notifcn)
        for filed in cls.json_fileds:
            kw.update({filed: json.dumps(kw[filed])})

        def query():
            return cls.rdbms_call('''
INSERT INTO "case_user_cc"
            (case_id,
             user_id,
             cfg)
VALUES      ( (SELECT id FROM "case" WHERE  name = :case_name),
              (SELECT id FROM "user" WHERE  login = :user_login),
              :cfg)
RETURNING *''', kw)
        try:
            rv = query()
        except exc.IntegrityError as e:
            if 'already exists' in str(e):
                raise StorageError('Entrie allready exists')
            elif 'null value in column "user_id"' in str(e):
                raise StorageError(
                    'unknown *user_login* value:{}'.format(
                        kw.get('user_login')))
            raise StorageError('Some kind of IntegrityError')

        n = dict(zip(rv.keys(), rv.fetchall().pop()))
        n.update({
            'case_name': kw.get('case_name'),
            'user_login': kw.get('user_login'),
        })
        return NotifcnBuilder.from_row(**n)

    @classmethod
    def update(cls, case_name, user_login, cfg):
        q_params = {
            'case_name': case_name,
            'user_login': user_login,
            'cfg': json.dumps(cfg)
        }

        def query():
            q_stmt = '''UPDATE "case_user_cc"
SET cfg=:cfg
WHERE
    user_id = (SELECT id FROM "user" WHERE login = :user_login)
    AND case_id = (SELECT id FROM "case" WHERE  name = :case_name)

RETURNING cfg'''
            return cls.rdbms_call(q_stmt, q_params)

        try:
            cfg = [r for r in query()].pop()[0]
        except exc.IntegrityError:
            raise StorageError('Some kind of IntegrityError')
        n = {
            'case_name': case_name,
            'user_login': user_login,
            'cfg': cfg,
        }
        return NotifcnBuilder.from_row(**n)

    @classmethod
    def get_many(cls, **kw):
        """pagination"""
        pagination_stmt = '\nLIMIT :limit OFFSET :offset'
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

        filter_stmt = []
        if kw.get('user_login'):
            filter_stmt.append("""
AND user_id = (SELECT id FROM "user" WHERE login = :user_login)""")
            query_params['user_login'] = kw.get('user_login')
        if kw.get('case_name'):
            filter_stmt.append("""
AND case_id = (SELECT id FROM "case" WHERE  name = :case_name)""")
            query_params['case_name'] = kw.get('case_name')

        if filter_stmt:
            #filter_stmt = 'WHERE' + '\n'.join(filter_stmt)
            filter_stmt = '\n'.join(filter_stmt)
        else:
            filter_stmt = ''

        q_stmt = """
SELECT  n.*,
        c.name AS case_name,
        u.login AS user_login
FROM
        case_user_cc n,
        "case" c,
        "user" u

WHERE
        n.case_id = c.id
        AND n.user_id = u.id
{}
{}
"""
        rv = cls.rdbms_call(q_stmt.format(filter_stmt, pagination_stmt),
                            query_params)

        rows = rv.fetchall()
        if len(rows) == 0:
            return None, None, None, None

        elif len(rows) < per_page:  # last chunk of data
            next_page = None

        def create_notifcn(row):
            n_kw = dict(zip(rv.keys(), row))
            return NotifcnBuilder.from_row(**n_kw)

        return map(create_notifcn, rows), per_page, next_page, prev_page

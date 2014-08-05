# -*- encoding: utf-8 -*-

"""
    lunaport.dao.user
    ~~~~~~~~~~~~~~~~~

    Application users accounts.
"""
from sqlalchemy import text, exc
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from lunaport_worker.tasks.hooks import on_user_add 
from ..wsgi import app, db
from .. domain.user import UserBuilder
from exceptions import StorageError


class Dao(object):
    """Interface for user storage"""
    @classmethod
    def insert(cls, user):
        raise NotImplemented()

    @classmethod
    def get_by_login(cls, login, is_privat=False):
        raise NotImplemented()

    @classmethod
    def get_many(cls, **kw):
        raise NotImplemented()

    @classmethod
    def does_exist(cls, login):
        raise NotImplemented()

    @classmethod
    def get_names_butch(cls):
        raise NotImplemented()

class RDBMS(Dao):
    json_fileds = ['settings']
    per_page_default = app.config.get('USERS_PER_PAGE_DEFAULT') or 10
    per_page_max = app.config.get('USERS_PER_PAGE_MAX') or 100
    select_join_part = '''
SELECT  i.*,
        r.login AS reporter_login,
        a.login AS assignee_login
FROM    issue i,
        "user" r,
        "user" a
WHERE   i.id != 1
        AND i.reporter = r.id
        AND i.assignee = a.id'''

    @classmethod
    def rdbms_call(cls, q_test, q_params):
        return db.engine.connect().execute(text(q_test), **q_params)

    @classmethod
    def insert(cls, user):
        q_params = user.as_dict()

        def query():
            return cls.rdbms_call('''
INSERT INTO "user"
            (login,
             first_name,
             last_name,
             email,
             is_staff,
             is_superuser,
             is_robot)
VALUES      (:login,
             :first_name,
             :last_name,
             :email,
             :is_staff,
             :is_superuser,
             :is_robot)
RETURNING login''', q_params)
        try:
            login = [r for r in query()].pop()[0]
        except exc.IntegrityError as e:
            dupl_err = 'user with login {} allready exists'
            if 'already exists' in str(e):
                raise StorageError(
                    dupl_err.format(q_params.get('login')))
            raise StorageError('Some kind of IntegrityError')
        return login

    @classmethod
    def get_by_login(cls, login, is_privat=False):
        query_params = {
            'login': login
        }

        query_text = '''SELECT * FROM "user" WHERE login = :login'''
        rv = cls.rdbms_call(query_text, query_params)
        row = rv.first()
        if not row:
            return None

        usr_kw = dict(zip(rv.keys(), row))
        return UserBuilder.from_row(is_privat, **usr_kw)

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
        # Not implemented yet

        query_text = '''SELECT * FROM "user"'''
        rv = cls.rdbms_call(
            ''.join([query_text, pagination_part]),
            query_params)

        rows = rv.fetchall()
        if len(rows) == 0:
            return None, None, None

        def create_usr(row):
            usr_kw = dict(zip(rv.keys(), row))
            #return domain.UserBuilder.from_row(False, **usr_kw)
            return UserBuilder.from_row(False, **usr_kw)

        return map(create_usr, rows), per_page, next_page

    @classmethod
    def does_exist(cls, login):
        query_txt = '''select count(*) from "user" where "login" = :login'''
        rv = cls.rdbms_call(query_txt, {'login': login})
        if [row[0] for row in rv].pop() == 1:
            return True
        return False

    @classmethod
    def get_names_butch(cls):
        rv = cls.rdbms_call(
            'select login from "user" order by login', {})
        return [el[0] for el in rv.fetchall()]


class SideEffect(Dao):
    """Side effect wrapper, implementing test.dao interface.
    """
    def __init__(self, dao):
        self.dao = dao

    def insert(self, user):
        login = self.dao.insert(user)
        on_user_add.apply_async(args=[login])
        return login 

    def get_by_login(self, login, **kw):
        return self.dao.get_by_login(login, **kw)

    def get_many(self, **kw):
        return self.dao.get_many(login, **kw)

    def does_exist(self, login):
        return self.dao.does_exist(login)

    def get_names_butch(cls):
        return self.dao.get_names_butch()



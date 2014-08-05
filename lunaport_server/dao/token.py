# -*- encoding: utf-8 -*-

"""
    lunaport.dao.token
    ~~~~~~~~~~~~~~~~~~

    Storage interaction logic for authentication token.
"""

from hashlib import sha1
import string
import random
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from sqlalchemy import text, exc
from exceptions import StorageError

from ..wsgi import db
from .. domain.token import TokenBuilder, TokenAdaptor


class Token(object):
    @staticmethod
    def cmpl_hash(lst):
        return sha1(''.join(lst)).hexdigest()

    @staticmethod
    def rdbms_call(q_test, q_params):
        return db.engine.connect().execute(text(q_test), **q_params)

    @classmethod
    def exists(cls, value):
        query_txt = '''select count(*) from token where value =:value'''
        rv = cls.rdbms_call(query_txt, {'value': value})

        if [row[0] for row in rv].pop() == 1:
            return True
        return False

    @classmethod
    def meet(cls, name, passwd):
        """
        Check is user provided auth token valid or not.
        """
        cmpl_pwd = lambda lst: sha1(''.join(lst)).hexdigest()
        query_txt = '''select sault, hash from token where name =:name'''
        rv = cls.rdbms_call(query_txt, {'name': name})

        auth_pairs = [el for el in rv]  # tuple (sault, hash)
        if not auth_pairs:
            return False

        pair = auth_pairs.pop()
        if cmpl_pwd([name, passwd, pair[0]]) == pair[1]:
            #return True
            return name.split('_')[0]
        return False

    @classmethod
    def get_many(cls, login):
        query_stmt = '''
SELECT id, name, descr FROM token
WHERE owner_id = (SELECT id FROM "user" WHERE login = :login)'''
        rv = cls.rdbms_call(query_stmt, {'login': login})

        rows = rv.fetchall()
        if len(rows) == 0:
            return None

        #return [dict(zip(rv.keys(), row)) for row in rows]
        build = lambda t: TokenBuilder.from_row(**t)
        return map(build, (dict(zip(rv.keys(), row)) for row in rows))

    @classmethod
    def insert(cls, token):
        kw = TokenAdaptor.to_dict(token)
        _orig_set = string.ascii_uppercase + string.lowercase + string.digits
        _rnd_str = lambda cnt: ''.join(random.choice(_orig_set) for x in xrange(cnt))
        kw.update({
            'name': '{}_{}'.format(kw['login'], _rnd_str(15)),
            'sault': _rnd_str(15),
            'passwd': _rnd_str(15),
        })
        kw['hash'] = cls.cmpl_hash([kw['name'], kw['passwd'], kw['sault']])

        query_stmt = '''
INSERT INTO "token"
    (name, sault, hash, responsible_id, owner_id, permission_id, descr)
VALUES
    (:name,
     :sault,
     :hash,
     (SELECT id from "user" WHERE login = :login),
     (SELECT id from "user" WHERE login = :login),
     3,
     :descr)
RETURNING id
'''
        try:
            rv = cls.rdbms_call(query_stmt, kw)
        except exc.IntegrityError:
            raise StorageError('Some kind of IntegrityError')

        t = dict(zip(rv.keys(), rv.fetchall().pop()))
        t.update({
            'name': kw.get('name'),
            'passwd': kw.get('passwd'),
            'descr': kw.get('descr'),
        })
        return TokenBuilder.from_row(**t)

    @classmethod
    def delete(cls, token_id, login):
        query_params = {
            'token_id': token_id,
            'login': login,
        }
        query_stmt = '''
DELETE FROM token WHERE
    owner_id = (SELECT id FROM "user" WHERE login = :login)
    AND id = :token_id
RETURNING id'''
        try:
            rv = cls.rdbms_call(query_stmt, query_params)
        except exc.IntegrityError:
            raise StorageError('Some kind of IntegrityError')

        if len(rv.fetchall()) < 1:
            raise ValueError('Inconsistent pair of values: token_id and user login.')
        return True

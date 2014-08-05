# -*- encoding: utf-8 -*-

"""
    lunaport.dao.host
    ~~~~~~~~~~~~~~~~~
    Storage interaction logic for host resource.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from sqlalchemy import text, exc

from ..wsgi import app, db
from .. domain.host import HostBuilder, HostAdaptor
from exceptions import StorageError


class Dao(object):
    @classmethod
    def insert(cls, case):
        raise NotImplemented()

    @classmethod
    def get_by_fqdn(cls, **kw):
        raise NotImplemented()

    @classmethod
    def get_many(cls, **kw):
        raise NotImplemented()

    @classmethod
    def get_names_butch(cls):
        raise NotImplemented()

    @classmethod
    def update_by_name(cls, host_name, host_diff):
        raise NotImplemented()

    @classmethod
    def update_or_create(cls, host_entrie):
        raise NotImplemented()


class SQLBuilder(object):
    params_allowed = {
        'line': (
            'AND l.name = :line',
            'AND l.name = ANY (:line)'),
        'dc': (
            'AND l.dc_id = (select id from dc where name = :dc)',
            'AND l.dc_id = ANY (select id from dc where name = ANY (:dc))'),
        'is_spec_tank': (
            'AND s.is_spec_tank = :is_spec_tank',
            None),
        'is_tank': (
            'AND s.is_tank = :is_tank',
            None),
        'ip_addr': (
            'AND s.ip_addr = :ip_addr',
            'AND s.ip_addr = ANY (:ip_addr)',)
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


class RDBMS(Dao):
    per_page_default = app.config.get('HOST_PER_PAGE_DEFAULT') or 10
    per_page_max = app.config.get('HOST_PER_PAGE_MAX') or 100
    insert_part = '''
INSERT INTO server
            (fqdn,
             added_at,
             ip_addr,
             is_spec_tank,
             is_tank)
VALUES
            (:fqdn,
             now(),
             :ip_addr,
             :is_spec_tank,
             :is_tank)'''

#    select_part = '''
#SELECT s.*,
#       l.name        AS line_name
#FROM   server s,
#       line l
#WHERE  s.line_id = l.id
#       AND s.fqdn = :fqdn'''
    select_part = '''
SELECT s.*,
       l.name        AS line_name
FROM   server s,
       line l
WHERE  s.line_id = l.id'''


    update_top = '''UPDATE server
SET
'''
    update_bottom = '''
WHERE  fqdn = :fqdn'''
#RETURNING id'''

    @staticmethod
    def rdbms_call(q_test, q_params):
        return db.engine.connect().execute(text(q_test), **q_params)

    @classmethod
    def cmpl_update_sql(cls, host_diff):
        rv = []
        attr_allowed = [
            'descr',
            'line_name',
            'is_spec_tank',
            'is_tank',
            'host_serv'
        ]
        for attr in attr_allowed:
            if not host_diff.get(attr) is None:
                if attr == 'line_name':
                    rv.append('''
line_id = (SELECT id
FROM "line"
WHERE name = :line_name
union all
select -1
where not exists (select 1 from "line" where name = :line_name))''')
                else:
                    rv.append('{} = :{}'.format(attr, attr))

        return ''.join([
            cls.update_top,
            ',\n'.join(rv),
            cls.update_bottom,
        ])

    @classmethod
    def insert(cls, host):
        query_params = HostAdaptor.to_dict(host)
        try:
            rv = cls.rdbms_call(' '.join([cls.insert_part, 'RETURNING id']), query_params)
            pk_id = [r for r in rv].pop()[0]
        except exc.IntegrityError as e:
            if 'violates unique constraint "server_fqdn_key"' in str(e):
                raise StorageError('server with such *fqdn* allready exists:{}'.format(
                                   query_params.get('fqdn')))
            raise StorageError('Some kind of IntegrityError')
        return pk_id

    @classmethod
    def get_by_fqdn(cls, **kw):
        query_params = {
            'fqdn': kw.get('fqdn'),
        }

        rv = cls.rdbms_call(cls.select_part + '\nAND s.fqdn = :fqdn\nlimit 1', query_params)
        row = rv.first()
        if not row:
            return None

        rv_dict = dict(zip(rv.keys(), row))
        return HostBuilder.from_row(**rv_dict)

    @classmethod
    def get_many(cls, **kw):
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

        cond_part, q_params_up = SQLBuilder(**kw).cmpl_query()
        query_params.update(q_params_up)

        try:
            rv = cls.rdbms_call(
                ''.join([cls.select_part, cond_part, pagination_part]), query_params)
            rows = rv.fetchall()
        except exc.IntegrityError:
            raise StorageError('Some kind of IntegrityError')
        except exc.DataError as e:
            if 'invalid input syntax for type inet' in str(e):
                raise ValueError('Wrong *ip_addr* param type') 

            raise StorageError('One of params malformed or has a wrong type')

        if len(rows) == 0:
            return None, None, None, None
        elif len(rows) < per_page:  # last chunk of data
            next_page = None

        def create_host(row):
            h_kw = dict(zip(rv.keys(), row))
            return HostBuilder.from_row(**h_kw)

        return map(create_host, rows), per_page, next_page, prev_page


    @classmethod
    def get_names_butch(cls):
        rv = cls.rdbms_call(
            'select fqdn from server order by fqdn', {})
        return [el[0] for el in rv.fetchall()]

    @classmethod
    def update_by_name(cls, host_name, host_diff):
        q_params = host_diff
        q_params.update({
            'fqdn': host_name,
        })
        try:
            cls.rdbms_call(cls.cmpl_update_sql(host_diff) + '\nRETURNING id', host_diff)
        except exc.IntegrityError:
            raise StorageError('Some kind of IntegrityError')
        return cls.get_by_fqdn(fqdn=host_name)

    @classmethod
    def update_or_create(cls, host_entrie):
        q_params = HostAdaptor.to_dict(host_entrie)
        condition_part = '''
INSERT INTO server
            (fqdn,
             added_at,
             ip_addr,
             is_spec_tank,
             is_tank)
SELECT
             :fqdn,
             now(),
             :ip_addr,
             :is_spec_tank,
             :is_tank
WHERE NOT EXISTS (SELECT 1 FROM server WHERE fqdn=:fqdn)
'''
        q_text = cls.cmpl_update_sql(q_params) + ';\n' + condition_part
        cls.rdbms_call(q_text + ' RETURNING id', q_params)
        return cls.get_by_fqdn(fqdn=q_params['fqdn'])

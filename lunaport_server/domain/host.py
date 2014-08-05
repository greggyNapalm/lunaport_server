# -*- encoding: utf-8 -*-

"""
    lunaport.domain.host
    ~~~~~~~~~~~~~~~~~~~~
    Bbusiness logic layer for host resource.
"""

import pprint
import copy
import socket
pp = pprint.PrettyPrinter(indent=4).pprint

from .. helpers import validate_net_addr
from base import BaseAdaptor, BaseEntrie


class Host(BaseEntrie):
    """ Host in lunaport terminology means physical/virtual server
        which can be used as load generator or testing target.
    """
    attr_required = [
        'fqdn',
        'ip_addr',
    ]
    attr_optional = [
        'id',
        'added_at',
        'descr',
        'line_id',
        'line_name',
        'is_spec_tank',
        'is_tank',
    ]
    attr_date = ['added_at']

    def __repr__(self):
        return '<domain.host #{} {}>'.format(getattr(self, 'id'), self.fqdn)


class HostBuilder(object):
    """Host instance static builder.
    """
    req_attr_allowed = [
        'fqdn',
        'ip_addr',
        'is_spec_tank',
        'is_tank',
    ]
    req_attr_allowed_set = set(req_attr_allowed)

    @classmethod
    def from_Flask_req(cls, r):
        """Creates class instance from Flask request object.
        Args:
            r: Flask request object.

        Returns:
            Host class instance.
        """
        if r.mimetype == 'multipart/form-data':
            msg_rv = r.form

        elif r.mimetype == 'application/json':
            msg_rv = r.json
        else:
            raise ValueError('Unsupported mime type')

        if not msg_rv:
            raise ValueError('Can\'t deserialize request body')

        # ImmutableMultiDict to dict cast
        msg_rv = dict((k, v) for k, v in msg_rv.items())
        msg_set = set(msg_rv.keys())

        if not msg_set.issubset(cls.req_attr_allowed_set):
            err_msg = [
                'Body contains unexpected params:',
                str(list(msg_set - cls.req_attr_allowed_set))
            ]
            raise ValueError(' '.join(err_msg))

        return cls.from_addr(**msg_rv)

    @classmethod
    def from_addr(cls, fqdn=None, ip_addr=None, unknown_addr=None,
                  is_spec_tank=False, is_tank=False):
        """
        Creates class Host instance from FQDN and/or ip_addr.
        Args:
            fqdn: str, Fully Qualified Domain Name.
            ip_addr: str, Internet Protocol address.
            unknown_addr: str, IPv4 or IPv6 or FQDN. Yandex-tank allow user to
            call tool with one that addr as a Phantom section param. It's
            server side task to determine which add type was provided.

        Returns:
            Host class instance.

        Throws:
            ValueError
        """
        def resolve(fqdn):
            try:
                return socket.getaddrinfo(fqdn, None).pop()[-1][0]
            except socket.gaierror:
                raise ValueError(
                    'Unresolvable hostname:*{}* try to use fqdn or ip_addr instead'.format(fqdn))
        if unknown_addr:
            if validate_net_addr(unknown_addr):
                try:
                    params = {
                        'fqdn': socket.gethostbyaddr(unknown_addr)[0],
                        'ip_addr': unknown_addr,
                    }
                except:
                    params = {
                        'fqdn': 'EXAMPLE.COM',
                        'ip_addr': unknown_addr,
                    }
            else:
                params = {
                    'fqdn': unknown_addr,
                    'ip_addr': resolve(unknown_addr),
                }
        elif fqdn and ip_addr:
            params = {
                'fqdn': fqdn,
                'ip_addr': ip_addr,
            }
        elif fqdn:
            try:
                params = {
                    'fqdn': fqdn,
                    'ip_addr': socket.gethostbyname_ex(fqdn)[-1].pop()
                }
            except socket.gaierror:
                raise ValueError('Can\'t resolve provided *fqdn*')
        elif ip_addr:
            try:
                params = {
                    'fqdn': socket.gethostbyaddr(ip_addr)[0],
                    'ip_addr': ip_addr,
                }
            except:
                params = {
                    'fqdn': 'EXAMPLE.COM',
                    'ip_addr': ip_addr,
                }
        else:
            raise ValueError(
                'at least one of params: fqdn, ip_addr should be specified')

        params.update({
            'is_tank': is_tank,
            'is_spec_tank': is_spec_tank,
        })
        return Host(**params)

    @classmethod
    def from_row(cls, **row):
        """Creates class instance from RDBMS returned row.
        Args:
            row: dict with table columns as keys.

        Returns:
            Host class instance.
        """
        return Host(**row)


class HostAdaptor(BaseAdaptor):
    @classmethod
    def to_dict(cls, host_entrie, date_iso=False):
        rv = copy.deepcopy(host_entrie.__dict__)

        if 'line_id' in rv.keys():
            rv['line'] = {'id': rv['line_id']}
            del rv['line_id']

        if 'line_name' in rv.keys():
            rv['line']['name'] = rv['line_name']
            del rv['line_name']

        if date_iso:  # datetime obj JSON serializable in ISO 8601 format.
            for attr in host_entrie.attr_date:
                if rv.get(attr):
                    rv[attr] = rv[attr].isoformat()
        return rv

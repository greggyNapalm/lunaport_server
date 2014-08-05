# -*- encoding: utf-8 -*-

"""
    lunaport.domain.proj
    ~~~~~~~~~~~~~~~~~~~~
    Bbusiness logic layer for project resource.
"""

import json
import copy
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from ..wsgi import app
from lunaport_worker.clients import (
    JIRARESTClinet,
    BaseClinetError,
)


class ProjProviderAdaptor(object):
    """ Basic class for project data provider like:
        JIRA client, some client, etc.
    """
    default_cfg = {
        'TO': 10.0,  # HTTP call timeout in seconds
    }
    proj_stract = {  # retval stract for fetch call
        'name': None,
        'title': None,
        'descr': None,  # unicode
        'reporter': None,
        'assignee': None,
        'closed': None,  # bool
        'provider': None,
        'project': None,
    }

    class __metaclass__(type):
        __inheritors__ = {}

        def __new__(meta, name, bases, dct):
            klass = type.__new__(meta, name, bases, dct)
            for base in klass.mro()[1:-1]:
                meta.__inheritors__[klass.name] = klass
            return klass

    def __init__(self, usr_cfg):
        self.cfg = copy.deepcopy(self.default_cfg)
        self.cfg.update(usr_cfg)

    def fetch(proj_name):
        raise NotImplementedError('inheritance only')


class JIRAAdaptor(ProjProviderAdaptor):
    """ Adaptor for JIRA REST client
    """
    name = 'JIRA'
    fields_to_fetch = [
        'reporter',
        'assignee',
        'created',
        'description',
        'status',
        'project',
        'components',
        'status',
        'summary',
    ]
    fields = ','.join(fields_to_fetch)
    status_closed_ids = ['6']

    def __init__(self, usr_cfg):
        self.cfg = copy.deepcopy(self.default_cfg)
        self.cfg.update(usr_cfg)

        assert all([
            'HOST' in self.cfg,
            'TO' in self.cfg,
            'OAUTH' in self.cfg,
        ]), 'Malformed usr_cfg struct'

        self.c = JIRARESTClinet(fqdn=self.cfg['HOST'], oauth=self.cfg['OAUTH'],
                                to=30)

    def fetch(self, proj_name):
        """ Call remote JIRA data provider to fetch proj details.
        """
        proj_name = proj_name.lower()
        try:
            rv = self.c.proj(proj_name, fields=self.fields)
            return self.compose_ret_data(proj_name, rv)
        except BaseClinetError:
            return None

    def compose_ret_data(self, proj_name, msg):
        """ Convert JIRA client project data msg in to common adapters format.
        """
        proj = copy.copy(self.proj_stract)
        try:
            proj.update({
                'name': proj_name,
                'provider': 'jira',
                'lead': msg['lead']['name'],
                'descr': msg['description'],
            })
        except Exception:
            raise ValueError('JIRA proj data  provider returns malformed data.')
        return proj


class ProjAdaptor(object):
    """ Adapt Proj instance.
    """
    @staticmethod
    def to_resp(proj, jsonify=True):
        """
        HTTP resp suitable representation.
        """
        rv = proj.as_dict(date_iso=True)
        if jsonify:
            return json.dumps(rv)
        else:
            return rv


class Proj(object):
    """ Project - issue tracker(jira, some, etc) project term.
    """
    attr_required = [
        'name',
        'provider',
    ]
    attr_optional = [
        'id',
        'lead',
        'added_at',
        'descr',
    ]
    attr_date = ['added_at']

    def __init__(self, **kw):
        for attr in self.attr_required:
            v = kw.get(attr)
            if not v:
                raise ValueError(
                    '*{}* - required parameter missing.'.format(attr))
            setattr(self, attr, v)

        for attr in self.attr_optional:
            setattr(self, attr, kw.get(attr))

    def as_dict(self, date_iso=False):
        retval = self.__dict__
        if date_iso:  # datetime obj JSON serializable in ISO 8601 format.
            for attr in self.attr_date:
                if retval.get(attr):
                    retval[attr] = retval[attr].isoformat()
        return retval

    def as_json(self):
        return json.dumps(self.as_dict(date_iso=True))


class ProjBuilder(object):
    """ Statis fabric for project obj.
    """
    req_attr_allowed = [
        'name',
        'provider',
    ]
    req_attr_allowed_set = set(req_attr_allowed)

    proj_adaptors = []
    registered_adaptors = ProjProviderAdaptor.__inheritors__
    enabled_adaptors = app.config['PROJ_PROVIDERS']
    if not enabled_adaptors:
        raise ValueError('*PROJ_PROVIDERS* app config section required')
    for name, cfg in enabled_adaptors.iteritems():
        proj_adaptors.append(registered_adaptors[name](cfg))

    @classmethod
    def from_Flask_req(cls, r):
        """ Creates class instance from Flask request object.
        Args:
            r: Flask request object.

        Returns:
            Proj class instance.
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

        return cls.from_name(msg_rv['name'])

    @classmethod
    def from_name(cls, name):
        """
        Creates Project class instance from *name* field value.
        Args:
            name: str, uniq name value.

        Returns:
            Proj class instance.
        """
        proj_data = cls.fetch_proj_details(name)
        if not proj_data:
            raise ValueError(
                'No such proj in proj providers:{}'.format(name))
        return Proj(**proj_data)

    @classmethod
    def fetch_proj_details(cls, proj_name):
        for a in cls.proj_adaptors:
            rv = a.fetch(proj_name)
            if rv:
                return rv
        return None  # proj missing in all sources


    @classmethod
    def from_row(cls, **row):
        """ Creates class instance from RDBMS returned row.
        Args:
            row: dict with table columns as keys.

        Returns:
            Proj class instance.
        """
        return Proj(**row)

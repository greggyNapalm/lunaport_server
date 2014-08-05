# -*- encoding: utf-8 -*-

"""
    lunaport.domain.issue
    ~~~~~~~~~~~~~~~~~~~~~
    Bbusiness logic layer for issue resource.
"""

import json
import copy
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from ..wsgi import app
from lunaport_worker.clients import (
    JIRARESTClinet,
    #someClinet,
    BaseClinetError,
)


class IssueAdaptor(object):
    """ Basic class for adaptor for issue provider like:
        JIRA client, Redmine client, etc.
    """
    default_cfg = {
        'TO': 10.0,  # HTTP call timeout in seconds
    }
    issue_stract = {  # retval stract for fetch call
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

    def fetch(issue_name):
        raise NotImplementedError('inheritance only')

    def add_comment(issue_name, comment_txt):
        raise NotImplementedError('inheritance only')


class JIRAAdaptor(IssueAdaptor):
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
                                to=20)

    def fetch(self, issue_name):
        """ Call remote JIRA data provider to fetch issue details.
        """
        issue_name = issue_name.lower()
        try:
            rv = self.c.issue(issue_name, fields=self.fields)
            return self.compose_ret_data(issue_name, rv)
        except BaseClinetError:
            return None

    def compose_ret_data(self, issue_name, msg):
        """ Convert JIRA client issue data msg to common adapters format.
        """
        issue = copy.copy(self.issue_stract)
        try:
            msg = msg['fields']
            issue.update({
                'name': issue_name,
                'title': msg['summary'],
                'descr': msg['description'],
                'reporter': msg['reporter']['name'],
                'assignee': msg['assignee']['name'],
                'closed': msg['status']['id'] in self.status_closed_ids,
                'provider': 'jira',
                'project': msg['project']['key'].lower(),
            })
        except Exception:
            raise ValueError('JIRA issue provider returns malformed data.')
        return issue


class Issue(object):
    """ Issue - task in issue tracker(jira, some, etc)
    """
    attr_required = [
        'name',
        'reporter',
        'assignee',
    ]
    attr_optional = [
        'id',
        'added_at',
        'title',
        'descr',
        'closed',
        'provider',
        'project',
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


class IssueBuilder(object):
    """ Issue instance static builder.
    """
    req_attr_allowed = [
        'name',
    ]
    req_attr_allowed_set = set(req_attr_allowed)

    issue_adaptors = []
    registered_adaptors = IssueAdaptor.__inheritors__
    enabled_adaptors = app.config['ISSUE_PROVIDERS']
    if not enabled_adaptors:
        raise ValueError('*ISSUE_PROVIDERS* app config section required')
    for name, cfg in enabled_adaptors.iteritems():
        issue_adaptors.append(registered_adaptors[name](cfg))

    @classmethod
    def from_Flask_req(cls, r):
        """ Creates class instance from Flask request object.
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
        return cls.from_name(msg_rv['name'])

    @classmethod
    def from_name(cls, name):
        """
        Creates Issue class instance from *name* field value.
        Args:
            name: str, uniq name value.

        Returns:
            Issue class instance.
        """
        issue_data = cls.fetch_issue_details(name)
        if not issue_data:
            raise ValueError(
                'No such issue in issue providers:{}'.format(name))
        return Issue(**issue_data)

    @classmethod
    def fetch_issue_details(cls, issue_name):
        for a in cls.issue_adaptors:
            rv = a.fetch(issue_name)
            if rv:
                return rv
        return None  # Issue missing in all sources


    @classmethod
    def from_row(cls, **row):
        """ Creates class instance from RDBMS returned row.
        Args:
            row: dict with table columns as keys.

        Returns:
            Issue class instance.
        """
        if 'reporter_login' in row:
            row['reporter'] = row['reporter_login']
        if 'assignee_login' in row:
            row['assignee'] = row['assignee_login']
        return Issue(**row)

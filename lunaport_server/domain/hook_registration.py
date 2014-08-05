# -*- encoding: utf-8 -*-

"""
    lunaport.domain.hook_registration
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    hook_registration - m2m connection case with hook. Rule to starte test.
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from base import BaseFactory, BaseAdaptor, BaseEntrie


class HookRegistration(BaseEntrie):
    """
    HookRegistration instance.
    """
    attr_required = [
        'case_id',
        'hook_id',
        'descr',
        'cfg',
        'owner',
    ]
    attr_optional = [
        'is_enabled',
        'hook_name',
        'id',
        'case',
        'added_at',
        'last_used_at'
    ]
    attr_date = ['added_at', 'last_used_at']


class HookRegistrationAdaptor(BaseAdaptor):
    attr_date = ['added_at', 'last_used_at']
    @classmethod
    def to_resp(cls, hook_registration, jsonify=True):
        """
        HTTP resp suitable representation.
        """
        rv = cls.to_dict(hook_registration, date_iso=True)
        if 'case' in rv.keys():
            rv['case'] = {'name': rv['case']}

        if 'case_id' in rv.keys():
            rv['case']['id'] = rv['case_id']
            del rv['case_id']

        if 'hook_name' in rv.keys():
            rv['hook'] = {'name': rv['hook_name']}
            del rv['hook_name']

        if 'hook_id' in rv.keys():
            rv['hook']['id'] = rv['hook_id']
            del rv['hook_id']


        if jsonify:
            return json.dumps(rv)
        else:
            return rv




class HookRegistrationBuilder(BaseFactory):
    """ HookRegistration instance builder.
    """
    req_attr_allowed = [
        'case_id',
        'hook_id',
        'descr',
        'cfg',
        'is_enabled'
    ]
    req_attr_allowed_set = set(req_attr_allowed)

    @classmethod
    def from_Flask_req(cls, r, session):
        """ Creates class instance from Flask request object.
        Args:
            r: Flask request object.
            session: Flask session object.

        Returns:
            HookRegistration class instance.
        """
        params = cls.parse_flask_req(r, session)
        params['owner'] = session.get('login', None)
        return HookRegistration(**params)

    @classmethod
    def from_row(cls, **row):
        """
        Creates class instance from RDBMS returned row.
        Args:
            row: dict with table columns as keys.

        Returns:
            Notifcn class instance.
        """
        return HookRegistration(**row)

# -*- encoding: utf-8 -*-

"""
    lunaport.domain.notification
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    DESC
"""

import pprint
import json
pp = pprint.PrettyPrinter(indent=4).pprint

from base import BaseFactory, BaseAdaptor, BaseEntrie


class Notifcn(BaseEntrie):
    attr_required = [
    ]
    attr_optional = [
        'cfg',
        'case_id',
        'user_id',
        'case_name',
        'user_login',
    ]


class NotifcnBuilder(BaseFactory):
    """ Notification instance static fabric.
    """
    req_attr_allowed = [
        'case_name',
        'user_login',
        'cfg',
    ]
    req_attr_allowed_set = set(req_attr_allowed)

    @classmethod
    def from_Flask_req(cls, r, session):
        """ Creates class instance from Flask request object.
        Args:
            r: Flask request object.
            session: Flask session object.

        Returns:
            Test class instance.
        """
        return Notifcn(**cls.parse_flask_req(r, session))

    @classmethod
    def from_row(cls, **row):
        """
        Creates class instance from RDBMS returned row.
        Args:
            row: dict with table columns as keys.

        Returns:
            Notifcn class instance.
        """
        return Notifcn(**row)


class NotifcnAdaptor(BaseAdaptor):
    attr_date = []

    @classmethod
    def to_resp(cls, notifcn, jsonify=True):
        """
        HTTP resp suitable representation.
        """
        rv = cls.to_dict(notifcn, date_iso=True)
        rv_tr = {
            'cfg': rv.get('cfg'),
            'case': {'name': rv.get('case_name'), 'id': rv.get('case_id')},
            'user': {'login': rv.get('user_login'), 'id': rv.get('user_id')}
        }
        if jsonify:
            return json.dumps(rv_tr)
        else:
            return rv_tr

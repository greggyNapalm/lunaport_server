# -*- encoding: utf-8 -*-

"""
    lunaport.domain.token
    ~~~~~~~~~~~~~~~~~~~~~
    Business logic layer for project token.
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from base import BaseFactory, BaseAdaptor, BaseEntrie


class Token(BaseEntrie):
    attr_required = [
        'descr',
    ]
    attr_optional = [
        'id',
        'name',
        'login',
        'passwd',
    ]


class TokenBuilder(BaseFactory):
    """ Token instance static fabric.
    """
    req_attr_allowed = [
        'descr',
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
        params = cls.parse_flask_req(r, session)
        params['login'] = session.get('login', None)
        return Token(**params)

    @classmethod
    def from_row(cls, **row):
        """
        Creates class instance from RDBMS returned row.
        Args:
            row: dict with table columns as keys.

        Returns:
            Notifcn class instance.
        """
        return Token(**row)


class TokenAdaptor(BaseAdaptor):
    attr_date = []

    @classmethod
    def to_resp(cls, token, jsonify=True):
        """
        HTTP resp suitable representation.
        """
        rv = cls.to_dict(token, date_iso=True)
        if jsonify:
            return json.dumps(rv)
        else:
            return rv

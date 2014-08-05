# -*- encoding: utf-8 -*-

"""
    lunaport.domain.case
    ~~~~~~~~~~~~~~~~~~~~
    DESC
"""

import pprint
import json
import copy
pp = pprint.PrettyPrinter(indent=4).pprint


class Case(object):
    """
    Tes case - contains info about test purpose, oracle(validation rules),
    notifications.
    """
    attr_required = [
        'name',
        'descr',
        'oracle',
    ]
    attr_optional = [
        'id',
        'added_at',
        'changed_at',
        'root_test_id',
        'etalon_test_id',
        'notification',
    ]
    attr_date = ['added_at', 'changed_at']

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
        retval = copy.deepcopy(self.__dict__)
        if date_iso:  # datetime obj JSON serializable in ISO 8601 format.
            for attr in self.attr_date:
                if retval.get(attr):
                    retval[attr] = retval[attr].isoformat()
        return retval

    def as_json(self):
        return json.dumps(self.as_dict(date_iso=True))

    def patch(self, diff):
        """
        Partially modify class instance.
        Args:
            diff: dict witk att-value pairs.

        Returns:
            Nothing.
        """
        for k, v in diff.iteritems():
            if not hasattr(self, k):
                raise ValueError('Unexpected *Test* diff keys:{}'.format(k))
            setattr(self, k, v)


class CaseBuilder(object):
    """
    Case instance static fabric.
    """
    req_attr_allowed = [
        'name',
        'descr',
        'oracle',
        'root_test_id',
        'etalon_test_id',
        'notification'
    ]
    req_attr_allowed_set = set(req_attr_allowed)

    @classmethod
    def from_Flask_req(cls, r, session):
        """
        Creates class instance from Flask request object.
        Args:
            r: Flask request object.
            session: Flask session object.

        Returns:
            Case class instance.
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
        for k, v in msg_rv.iteritems():
            if isinstance(v, list) and len(v) == 1:
                msg_rv[k] = v[0]

        return Case(**msg_rv)

    @classmethod
    def from_row(cls, **row):
        """ Creates class instance from RDBMS returned row.
        Args:
            row: dict with table columns as keys.

        Returns:
            YnadexTankTest class instance.
        """
        return Case(**row)

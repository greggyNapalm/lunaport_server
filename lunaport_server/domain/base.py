# -*- encoding: utf-8 -*-

"""
    lunaport.domain.base
    ~~~~~~~~~~~~~~~~~~~~
    Base domain static factory.
"""

import pprint
import json
import copy
pp = pprint.PrettyPrinter(indent=4).pprint

import pytz
import dateutil.parser


class BaseFactory(object):
    target_struct = None
    req_attr_allowed = []
    req_attr_allowed_set = set(req_attr_allowed)

    @classmethod
    def from_row(cls, **row):
        """Creates class instance from RDBMS returned row.
        Args:
            row: dict with table columns as keys.

        Returns:
            *target_struct* class instance.
        """
        return cls.target_struct(**row)

    @classmethod
    def from_Flask_req(cls, *arg, **kw):
        raise NotImplemented()

    @classmethod
    def parse_flask_req(cls, r, session):
        """ Creates dict from rquests body.
        Args:
            r: Flask request object.
            session: Flask session object.

        Returns:
            dict.
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

        return msg_rv


class BaseAdaptor(object):
    @classmethod
    def to_dict(cls, entrie, date_iso=False):
        retval = copy.deepcopy(entrie.__dict__)

        if date_iso:  # datetime obj JSON serializable in ISO 8601 format.
            for attr in entrie.attr_date:
                if retval.get(attr):
                    retval[attr] = retval[attr].isoformat()

        return retval

    @classmethod
    def to_json(cls, entrie):
        return json.dumps(cls.to_dict(entrie, date_iso=True))

    @classmethod
    def to_resp(cls, entrie, jsonify=True):
        """
        HTTP resp suitable representation.
        """
        rv = cls.to_dict(entrie, date_iso=True)
        if jsonify:
            return json.dumps(rv)
        else:
            return rv


class BaseEntrie(object):
    attr_required = []
    attr_optional = []
    attr_date = []

    def __init__(self, **kw):
        for attr in self.attr_required:
            v = kw.get(attr)
            if not v:
                raise ValueError(
                    '*{}* - required parameter missing.'.format(attr))
            setattr(self, attr, v)

        for attr in self.attr_optional:
            setattr(self, attr, kw.get(attr))

    def patch(self, diff):
        """
        Partially modify class instance.
        Args:
            diff: dict witk att-value pairs.
        """
        for k, v in diff.iteritems():
            if not hasattr(self, k):
                raise ValueError('Unexpected *entrie* diff keys:{}'.format(k))
            setattr(self, k, v)


def msk_iso_to_utc(date_iso_str):
    """ Convert 'Europe/Moscow' local time stamp to UTC stamp.
    """
    local = pytz.timezone('Europe/Moscow')
    local_dt = local.localize(dateutil.parser.parse(date_iso_str), is_dst=None)
    return local_dt.astimezone(pytz.utc)

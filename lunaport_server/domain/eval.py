# -*- encoding: utf-8 -*-
"""
    lunaport.domain.eval
    ~~~~~~~~~~~~~~~~~~~~
    Business logic layer for eval resource.
"""

import pprint
import json
pp = pprint.PrettyPrinter(indent=4).pprint


class Eval(object):
    """
    Test evaluation result - JSON document with asserts names, params, results.
    """
    attr_required = [
        'test_id',
        'oracle',
        'result',
        'passed'
    ]
    attr_optional = [
        'id',
        'added_at',
    ]
    attr_date = ['added_at']

    def __init__(self, **kw):
        for attr in self.attr_required:
            v = kw.get(attr, None)
            if v is None:
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


class EvalAdaptor(object):
    """ Adapt Eval instance.
    """
    @staticmethod
    def to_resp(t_eval, jsonify=True):
        """
        HTTP resp suitable representation.
        """
        rv = t_eval.as_dict(date_iso=True)
        if jsonify:
            return json.dumps(rv)
        else:
            return rv


class EvalBuilder(object):
    """
    Eval instance static builder.
    """
    req_attr_allowed = [
        'test_id',
        'result',
        'oracle',
        'passed',
    ]
    req_attr_allowed_set = set(req_attr_allowed)

    @classmethod
    def from_Flask_req(cls, r):
        """
        Creates class instance from Flask request object.

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

        return Eval(**msg_rv)

    @classmethod
    def from_row(cls, **row):
        """
        Creates class instance from RDBMS returned row.

        Args:
            row: dict with table columns as keys.

        Returns:
            Host class instance.
        """
        return Eval(**row)

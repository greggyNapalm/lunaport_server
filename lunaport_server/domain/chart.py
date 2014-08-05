# -*- encoding: utf-8 -*-
"""
    lunaport.domain.chart
    ~~~~~~~~~~~~~~~~~~~~~
    Business logic layer for chart resource.
"""

import pprint
import json
pp = pprint.PrettyPrinter(indent=4).pprint


class Chart(object):
    """
    Object encapsulate whole charts data calculated for test ^ ammo_tag pair.
    """
    attr_required = [
        'test_id',
        'ammo_tag',
        'version',
        'doc',
    ]
    attr_date = ['added_at']

    def __init__(self, **kw):
        for attr in self.attr_required:
            v = kw.get(attr)
            if not v:
                raise ValueError(
                    '*{}* - required parameter missing.'.format(attr))
            setattr(self, attr, v)

    def as_dict(self, date_iso=False):
        retval = self.__dict__
        if date_iso:  # datetime obj JSON serializable in ISO 8601 format.
            for attr in self.attr_date:
                if retval.get(attr):
                    retval[attr] = retval[attr].isoformat()
        return retval

    def as_json(self):
        return json.dumps(self.as_dict(date_iso=True))


class ChartBuilder(object):
    """
    Chart instance static builder.
    """
    req_attr_allowed = [
        'test_id',
        'version',
        'doc',
    ]
    req_attr_allowed_set = set(req_attr_allowed)

    @classmethod
    def ver_to_int(cls, version):
        """
        Adopt string version format like '0.1.4' to int representation.
        """
        return int(''.join(version.split('.')))

    @classmethod
    def from_Flask_req(cls, r, test_id, ammo_tag):
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

        msg_rv.update({
            'test_id': test_id,
            'ammo_tag': ammo_tag
        })
        msg_rv['version'] = cls.ver_to_int(msg_rv['version'])
        return Chart(**msg_rv)

    @classmethod
    def from_row(cls, **row):
        """
        Creates class instance from RDBMS returned row.

        Args:
            row: dict with table columns as keys.

        Returns:
            Host class instance.
        """
        return Chart(**row)

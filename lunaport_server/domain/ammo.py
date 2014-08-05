# -*- encoding: utf-8 -*-

"""
    lunaport.domain.ammo
    ~~~~~~~~~~~~~~~~~~~~
    descr
"""

import json
import copy
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint


class Ammo(object):
    """
    Load test input data.
    """
    attr_required = [
        'case',
        'owner',
    ]
    attr_optional = [
        'id',
        'case_id',
        'name',
        'file_storage',
        'path',
        'meta',
        'hash',
        'descr',
        'added_at',
        'last_used_at',
    ]
    attr_date = ['added_at', 'last_used_at']

    def __init__(self, **kw):
        for attr in self.attr_required:
            v = kw.get(attr)
            if not v:
                raise ValueError(
                    '*{}* - required parameter missing.'.format(attr))
            setattr(self, attr, v)

        for attr in self.attr_optional:
            setattr(self, attr, kw.get(attr))


class AmmoAdaptor(object):
    """ Adapt Ammo instance.
    """
    @classmethod
    def to_resp(cls, ammo, jsonify=True):
        """
        HTTP resp suitable representation.
        """
        keys_to_remove = [
            'file_storage',
        ]
        rv = cls.to_dict(ammo, date_iso=True)
        for k in keys_to_remove:
            try:
                del rv[k]
            except KeyError:
                pass

        if 'case' in rv.keys():
            rv['case'] = {'name': rv['case']}

        if 'case_id' in rv.keys():
            rv['case']['id'] = rv['case_id']
            del rv['case_id']
        if jsonify:
            return json.dumps(rv)
        else:
            return rv

    @staticmethod
    def to_dict(ammo, date_iso=False):
        retval = copy.deepcopy(dict(
            (k, v) for k, v in ammo.__dict__.iteritems() if k != 'file_storage'))
        if date_iso:  # datetime obj JSON serializable in ISO 8601 format.
            for attr in ammo.attr_date:
                if retval.get(attr):
                    retval[attr] = retval[attr].isoformat()
        return retval

    @classmethod
    def to_json(cls, ammo):
        return json.dumps(cls.to_dict(date_iso=True))


class AmmoBuilder(object):
    """ Ammo instance static fabric.
    """
    req_attr_allowed = [
        'case',
        'descr'
    ]
    req_attr_allowed_set = set(req_attr_allowed)
    f_names_allowed = ['ammo']

    @classmethod
    def from_Flask_req(cls, r, session):
        """ Creates class instance from Flask request object.
        Args:
            r: Flask request object.
            session: Flask session object.

        Returns:
            Ammo class instance.
        """
        if r.mimetype == 'multipart/form-data':
            msg_rv = r.form

        else:
            raise ValueError('Unsupported mime type')

        # ImmutableMultiDict to dict cast
        msg_rv = dict((k, v) for k, v in msg_rv.items())
        for k, v in msg_rv.iteritems():
            if isinstance(v, list) and len(v) == 1:
                msg_rv[k] = v[0]

        msg_set = set(msg_rv.keys())

        if not msg_set.issubset(cls.req_attr_allowed_set):
            err_msg = [
                'Body contains unexpected params:',
                str(list(msg_set - cls.req_attr_allowed_set))
            ]
            raise ValueError(' '.join(err_msg))

        if not r.files:
            raise ValueError('Request shude contains files:load_cfg and phout')

        if sorted(cls.f_names_allowed) != sorted(r.files.keys()):
            raise ValueError('Wrong files names in body.')

        msg_rv.update({
            'file_storage': r.files['ammo'],
            'name': r.files['ammo'].filename,
            'owner': session.get('login'),
        })
        return Ammo(**msg_rv)

    @classmethod
    def from_row(cls, **row):
        """Creates class instance from RDBMS returned row.
        Args:
            row: dict with table columns as keys.

        Returns:
            Ammo class instance.
        """
        return Ammo(**row)

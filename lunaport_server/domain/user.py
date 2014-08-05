# -*- encoding: utf-8 -*-

"""
    lunaport.domain.user
    ~~~~~~~~~~~~~~~~~~~~

    Business logic layer for user resource.
"""

import json
import copy
import pprint
pp = pprint.PrettyPrinter(indent=4)


class BasicUser(object):
    """User - service client, tests initiator and viewer.
    """
    attr_date = ['last_login', 'date_joined']

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


class UserPrivat(BasicUser):
    """What user(+admins) should know about itself.
    """
    attr_required = [
        'login',
        'first_name',
        'last_name',
        'email',
        'is_staff',
        'is_superuser',
        'is_robot',
    ]
    attr_optional = [
        'id',
        'settings',
        'last_login',
        'date_joined',
    ]


class UserPublic(BasicUser):
    """What other users should know about user.
       Used in API responces.
    """
    attr_required = [
        'login',
        'first_name',
        'last_name',
        'email',
    ]
    attr_optional = [
        'id',
        'last_login',
        'date_joined',
    ]


class UserBuilder(object):
    """User instance static builder.
    """
    req_attr_allowed = [
        'login',
    ]
    req_attr_allowed_set = set(req_attr_allowed)
    attr_fixture = {
        'first_name': 'fix',
        'last_name': 'fix',
        'email': 'fix',
        'is_staff': False,
        'is_superuser': False,
        'is_robot': False,
    }

    @classmethod
    def from_Flask_req(cls, r):
        """Creates class instance from Flask request object.
        Args:
            r: Flask request object.

        Returns:
            User class instance.
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

        # TODO: check user existence in 3rd party services
        return cls.from_login(msg_rv.get('login'))

    @classmethod
    def from_login(cls, login):
        """Creates class instance from *login* field value.
        Used to create user entrie without any additional info.
        Args:
            login: str, uniq user login.

        Returns:
            User class instance.
        """
        params = {'login': login}
        params = cls.complete_usr_data(usr_data=params)
        return UserPrivat(**params)

    @classmethod
    def public_from_priv(cls, priv_user_inst):
        return UserPublic(**priv_user_inst.__dict__)

    @classmethod
    def complete_usr_data(cls, usr_data):
        data = copy.deepcopy(cls.attr_fixture)
        data.update(usr_data)
        return data

    @classmethod
    def from_row(cls, is_privat, **row):
        """Creates class instance from RDBMS returned row.
        Args:
            row: dict with table columns as keys.

        Returns:
            Issue class instance.
        """
        if is_privat:
            return UserPrivat(**row)
        return UserPublic(**row)

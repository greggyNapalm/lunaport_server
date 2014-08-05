# -*- encoding: utf-8 -*-

"""
    lunaport.plugg_views.base
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Base class for Lunaport REST API class-based views.
"""

import copy
import urllib

from flask import request, jsonify
from flask.views import MethodView

from .. dao.exceptions import StorageError
from .. dao.user import RDBMS as dao_usr
from .. domain.user import UserBuilder
from .. dao.host import RDBMS as dao_host
from .. domain.host import HostBuilder
from .. dao.issue import RDBMS as dao_issue
from .. domain.issue import IssueBuilder
from .. dao.proj import RDBMS as dao_proj
from .. domain.proj import ProjBuilder


class BaseView(MethodView):
    str_params = []
    int_params = []

    @classmethod
    def cmpl_query(cls):
        query = {}
        for p, v in request.args.items():
            if p in cls.int_params:
                if not ((v.isdigit()) and (int(v) >= 0)):
                    raise ValueError('*{}* parameter malformed'.format(p))
                query.update({p: int(v)})

            if p in cls.str_params:
                v_spltd = v.split(',')
                if len(v_spltd) > 1:  # list of values in HTTP param
                    query.update({p: v_spltd})
                else:  # singular string param
                    query.update({p: str(v)})
        return query

    @staticmethod
    def cmpl_link_hdr(r, per_page, next_page, prev_page):
        link_hdr = []
        orig_qs = r.url.split('?')[0]
        orig_params = dict(r.args.items())

        def new_url(params_diff):
            p = copy.deepcopy(orig_params)
            p.update(params_diff)
            return '{}?{}'.format(orig_qs, urllib.urlencode(p))

        if next_page:
            link_hdr.append('<{}>; rel="next"'.format(new_url({
                'per_page': per_page,
                'page': next_page,
            })))
        if prev_page:
            link_hdr.append('<{}>; rel="prev"'.format(new_url({
                'per_page': per_page,
                'page': prev_page,
            })))
        return ','.join(link_hdr)

    @classmethod
    def autocomplete(cls, r_type, r_value):
        """
        Creates missing resource with dependent sources.
        Args:
            r_type: str, resource type aka Domain entrie name.
            r_value: str, resource identificator suitable for being static
                builder param.

        Returns:
            True - if resource was created successfully, False if not.
        """
        if r_type == 'user':
            try:
                user_priv = UserBuilder.from_login(r_value)
                user_priv.id = dao_usr.insert(user_priv)
                return True
            except (ValueError, StorageError) as e:
                return False
        elif r_type == 'host':
            try:
                host = HostBuilder.from_addr(unknown_addr=r_value)
                host.id = dao_host.insert(host)
                return True
            except (ValueError, StorageError) as e:
                return False
        elif r_type == 'proj':
            try:
                proj = ProjBuilder.from_name(r_value)
                proj.id = dao_proj.insert(proj)
                return True
            except (ValueError, StorageError) as e:
                return False
        elif r_type == 'issue':
            try:
                issue = IssueBuilder.from_name(r_value)
            except ValueError as e:
                return False
            try:
                issue.id = dao_issue.insert(issue)
                return True
            except StorageError as e:
                return cls.autocomplete(
                    getattr(e, 'missing_resource_type', None),
                    getattr(e, 'missing_resource_value', None))
        else:
            if r_type == 'case':
                # Case resource always must be created by user.
                # Current state mean that HTTP requests have mallformed param.
                raise ValueError('Unknown case value:{}'.format(r_value))
            raise ValueError('Unknown REST resource type:{}'.format(r_type))
        return False

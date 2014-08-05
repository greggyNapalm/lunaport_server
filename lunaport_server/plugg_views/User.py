# -*- encoding: utf-8 -*-

"""
    lunaport.plugg_views.user
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for User resource.
"""

import json
import urllib
import pprint
pp = pprint.PrettyPrinter(indent=4)

from flask import jsonify, request, Response, url_for, session, redirect
from flask.views import MethodView

from .. dao.exceptions import StorageError
from .. dao.user import RDBMS as dao_usr
from .. domain.user import UserBuilder


class User(MethodView):
    @staticmethod
    def cmpl_query():
        str_params = [
            'title',
            'descr',
            'reporter',
            'assignee',
        ]
        int_params = [
            'page',
            'per_page',
        ]
        query = {}
        for p, v in request.args.items():
            if p in int_params:
                if not ((v.isdigit()) and (int(v) >= 0)):
                    raise ValueError('*{}* parameter malformed'.format(p))
                query.update({p: int(v)})

            if p in str_params:
                v_spltd = v.split(',')
                if len(v_spltd) > 1:  # list of values in HTTP param
                    query.update({p: v_spltd})
                else:  # singular string param
                    query.update({p: str(v)})
        return query

    @staticmethod
    def get_param(name):
        if name in ['page', 'per_page']:
            v = request.args.get(name)
            if not v:
                return None
            if not ((v.isdigit()) and (int(v) >= 0)):
                raise ValueError('*{}* parameter error'.format(name))
            return int(v)

    @staticmethod
    def cmpl_location_hdr(per_page, page):
        url_cuted = request.url.split('?')[0]
        params = dict(request.args.items())
        params.update({
            'per_page': per_page,
            'page': page,
        })
        return '{}?{}'.format(url_cuted, urllib.urlencode(params))

    @staticmethod
    def get_names_butch(self):
            data = dao_usr.get_names_butch()
            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
            }
            if not data:
                return Response(status=404)
            return Response(response=json.dumps(data), status=200,
                            headers=hdrs)

    def get(self, login):
        if login is None:  # walk through all users
            if request.args.get('names_butch'):
                return self.get_names_butch(request)

            q = User.cmpl_query()
            try:

                users, per_page, page = dao_usr.get_many(**q)
            except StorageError as e:
                msg = {
                    'error_type': 'Storage call fails',
                    'error_text': str(e),
                }
                return jsonify(msg), 500
            except ValueError as e:
                msg = {
                    'error_type': 'Business logic layer error',
                    'error_text': str(e),
                }
                return jsonify(msg), 500

            if not users:
                return Response(status=404)

            body = json.dumps([u.as_dict(date_iso=True) for u in users])
            next_page_url = User.cmpl_location_hdr(per_page, page)
            hdrs = {
                'Link': '<{}>; rel="next"'.format(next_page_url),
                'Content-Type': 'application/json; charset=utf-8'
            }
            return Response(response=body, status=200,
                            headers=hdrs)
        else:  # try to get single *user* entrie by login
            try:
                user = dao_usr.get_by_login(login.lower())
            except StorageError as e:
                msg = {
                    'error_type': 'Storage call fails',
                    'error_text': str(e),
                }
                return jsonify(msg), 500

            if not user:
                return Response(status=404)

            hdrs = {'Content-Type': 'application/json; charset=utf-8'}
            return Response(response=user.as_json(), status=200, headers=hdrs)

    def post(self):
        try:
            user_priv = UserBuilder.from_Flask_req(request)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            user_priv.id = dao_usr.insert(user_priv)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        user = UserBuilder.public_from_priv(user_priv)

        hdrs = {
            'Location': '{}{}'.format(url_for('user'), user.login),
            'Content-Type': 'application/json; charset=utf-8',
        }
        return Response(response=user.as_json(), status=201, headers=hdrs)


class UserIdent(MethodView):
    def get(self):
        login = session.get('login', None)
        if login:
            return redirect('{}{}'.format(url_for('user'), login))
        else:
            return Response(status=401)

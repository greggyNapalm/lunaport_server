# -*- encoding: utf-8 -*-

"""
    lunaport.plugg_views.token
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Token API resource.
    Token - HTTP basic auth pair of username:password
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import jsonify, request, Response, url_for, session

from Base import BaseView
from .. dao.exceptions import StorageError
from .. dao.token import Token as dao_token
from .. domain.token import TokenBuilder, TokenAdaptor


class Token(BaseView):
    str_params = [
        'case_name',
        'user_login',
    ]
    int_params = [
        'page',
        'per_page',
    ]

    def get(self):
        try:
            tokens = dao_token.get_many(session.get('login', None))
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        if not tokens:
            return Response(status=404)

        body = json.dumps([TokenAdaptor.to_resp(t, jsonify=False) for t in tokens])
        hdrs = {
            'Content-Type': 'application/json; charset=utf-8',
        }
        return Response(response=body, status=200, headers=hdrs)

    def post(self):
        try:
            t = TokenBuilder.from_Flask_req(request, session)
        except (ValueError, AssertionError) as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            t = dao_token.insert(t)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        hdrs = {
            'Content-Type': 'application/json; charset=utf-8',
            'Location': '{}{}'.format(url_for('token'), t.id),
        }
        return Response(response=TokenAdaptor.to_resp(t), status=201,
                        headers=hdrs)

    def delete(self, token_id):
        try:
            dao_token.delete(token_id, session.get('login'))
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500
        except ValueError as e:
            msg = {
                'error_type': 'Malformed user provided data',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        return Response(status=200)

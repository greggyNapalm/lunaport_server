# -*- encoding: utf-8 -*-

"""
    lunaport.plugg_views.notification
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Notification API resource.
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import jsonify, request, Response, session

from Base import BaseView
from .. dao.exceptions import StorageError
from .. dao.notification import Notifcn as dao_notifcn
from .. domain.notification import NotifcnBuilder, NotifcnAdaptor


class Notifcn(BaseView):
    str_params = [
        'case_name',
        'user_login',
    ]
    int_params = [
        'page',
        'per_page',
    ]

    def get(self, case_name, user_login):
        if all([case_name, user_login]):
            q = {
                'case_name': case_name,
                'user_login': user_login,
            }
        else:
            q = self.cmpl_query()

        try:
            notifcns, per_page, next_page, prev_page = dao_notifcn.get_many(**q)
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

        if not notifcns:
            return Response(status=404)

        body = json.dumps(
            [NotifcnAdaptor.to_resp(n, jsonify=False) for n in notifcns])

        hdrs = {
            'Content-Type': 'application/json; charset=utf-8',
            'Link': self.cmpl_link_hdr(request, per_page, next_page,
                                       prev_page),
        }
        return Response(response=body, status=200,
                        headers=hdrs)
        hdrs = {'Content-Type': 'application/json; charset=utf-8'}
        return Response(response=NotifcnAdaptor.to_resp(n), status=200,
                        headers=hdrs)

    def post(self, user_login, case_name):
        try:
            n = NotifcnBuilder.from_Flask_req(request, session)
        except (ValueError, AssertionError) as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            n = dao_notifcn.insert(n)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        hdrs = {
            'Content-Type': 'application/json; charset=utf-8',
            #'Location': '{}'.format(url_for('notification')),
        }
        return Response(response=NotifcnAdaptor.to_resp(n), status=201,
                        headers=hdrs)

    def patch(self, case_name, user_login):
        """ Partially update of API resource.
        """
        cfg = request.json.get('cfg')
        if not cfg:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': 'Can\'t deserialize json document or *cfg param*',
            }
            return jsonify(msg), 422

        if not all([case_name, user_login]):
            msg = {
                'error_type': 'Malformed URL',
                'error_text': 'Unsupported  *case_name* and *user_login* values',
            }
            return jsonify(msg), 422

        try:
            n = dao_notifcn.update(case_name, user_login, cfg)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        hdrs = {
            'Content-Type': 'application/json; charset=utf-8',
            #'Location': '{}{}'.format(url_for('notification'), n.id),
        }
        return Response(response=NotifcnAdaptor.to_resp(n), status=200,
                        headers=hdrs)

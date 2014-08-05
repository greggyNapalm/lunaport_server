# -*- encoding: utf-8 -*-

"""
    lunaport.plugg_views.hook_registration
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for hook_registration resource.
    hook_registration - m2m connection case with hook. Rule to starte test.
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import jsonify, request, Response, url_for, session

from Base import BaseView
from .. dao.exceptions import StorageError
from .. dao.hook_registration import RDBMS
from .. domain.hook_registration import HookRegistrationBuilder, HookRegistrationAdaptor


class HookRegistration(BaseView):
    str_params = [
        'case_id',
        'hook_id',
        'descr',
        'cfg',
    ]
    dao = RDBMS

    def get(self, hook_registration_id=None):
        if hook_registration_id is None:  # walk through all registrations
            q = self.cmpl_query()
            try:
                h_regs, per_page, next_page, prev_page = self.dao.get_many(**q)
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

            if not h_regs:
                return Response(status=404)

            body = json.dumps(
                [HookRegistrationAdaptor.to_resp(r, jsonify=False) for r in h_regs])

            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
                'Link': self.cmpl_link_hdr(request, per_page, next_page,
                                           prev_page),
            }
            return Response(response=body, status=200,
                            headers=hdrs)
        else:  # try to get single *hook_registration* entrie by id
            try:
                h_regs = self.dao.get_single(hook_registration_id=hook_registration_id)
            except StorageError as e:
                msg = {
                    'error_type': 'Storage call fails',
                    'error_text': str(e),
                }
                return jsonify(msg), 500

            if not h_regs:
                return Response(status=404)

            hdrs = {'Content-Type': 'application/json; charset=utf-8'}
            return Response(response=HookRegistrationAdaptor.to_resp(h_regs), status=200,
                            headers=hdrs)

    def post(self):
        try:
            hook_registration = HookRegistrationBuilder.from_Flask_req(request, session)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            hook_registration.id = self.dao.insert(hook_registration)
            hook_registration = self.dao.get_single(hook_registration_id=hook_registration.id)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 409

        res_location = '{}{}'.format(url_for('hook_registration'), hook_registration.id)
        return Response(response=HookRegistrationAdaptor.to_resp(hook_registration), status=201,
                        headers={
                            'Location': res_location,
                            'Content-Type': 'application/json; charset=utf-8'
                        })

    def patch(self, hook_registration_id):
        diff = request.json
        if not diff:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': 'Can\'t deserialize json document',
            }
            return jsonify(msg), 422

        try:
            hook_registration = self.dao.update_by_id(hook_registration_id, diff)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        res_location = '{}{}'.format(url_for('hook_registration'), hook_registration.id)
        return Response(response=HookRegistrationAdaptor.to_resp(hook_registration), status=200,
                        headers={
                            'Location': res_location,
                            'Content-Type': 'application/json; charset=utf-8'
                        })

    def delete(self, hook_registration_id):
        try:
            self.dao.delete(hook_registration_id)
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

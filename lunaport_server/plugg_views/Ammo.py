# -*- encoding: utf-8 -*-

"""
    lunaport.plugg_views.ammo
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Ammo API resource.
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import jsonify, request, Response, url_for, session

from Base import BaseView
from .. dao.exceptions import StorageError
from .. dao.ammo import SideEffect, RDBMS
from .. domain.ammo import AmmoBuilder, AmmoAdaptor


class Ammo(BaseView):
    str_params = [
        'case',
        'owner',
        'hash',
        'path',
    ]
    int_params = [
        'page',
        'per_page',
    ]
    dao = SideEffect(RDBMS)

    def get(self, ammo_id):
        if ammo_id is None:  # walk through all ammo
            try:
                q = self.cmpl_query()
                ammos, per_page, next_page, prev_page = self.dao.get_many(**q)
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

            if not ammos:
                return Response(status=404)

            body = json.dumps(
                [AmmoAdaptor.to_resp(a, jsonify=False) for a in ammos])

            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
                'Link': self.cmpl_link_hdr(request, per_page, next_page,
                                           prev_page),
            }
            return Response(response=body, status=200,
                            headers=hdrs)
        else:  # try to get single *ammo* entrie by id
            try:
                ammo = self.dao.get_single(ammo_id=ammo_id)
            except StorageError as e:
                msg = {
                    'error_type': 'Storage call fails',
                    'error_text': str(e),
                }
                return jsonify(msg), 500

            if not ammo:
                return Response(status=404)

            hdrs = {'Content-Type': 'application/json; charset=utf-8'}
            return Response(response=AmmoAdaptor.to_resp(ammo), status=200,
                            headers=hdrs)

    def post(self):
        try:
            ammo = AmmoBuilder.from_Flask_req(request, session)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            ammo.id = self.dao.insert(ammo)
            ammo = self.dao.get_single(ammo_id=ammo.id)
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

        res_location = '{}{}'.format(url_for('ammo'), ammo.id)
        return Response(response=AmmoAdaptor.to_resp(ammo), status=201,
                        headers={
                            'Location': res_location,
                            'Content-Type': 'application/json; charset=utf-8'
                        })

    def patch(self, ammo_id):
        """ Partially update of API resource.
        """
        diff = request.json
        if not diff:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': 'Can\'t deserialize json document',
            }
            return jsonify(msg), 422

        try:
            ammo = self.dao.update_by_id(ammo_id, diff)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500
        except AssertionError as e:
            msg = {
                'error_type': 'Malformed request data',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        hdrs = {
            'Content-Type': 'application/json; charset=utf-8',
            'Location': '{}{}'.format(url_for('ammo'), ammo.id),
        }
        return Response(response=AmmoAdaptor.to_resp(ammo), status=200,
                        headers=hdrs)

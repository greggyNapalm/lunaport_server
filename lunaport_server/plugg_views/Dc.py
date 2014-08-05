# -*- encoding: utf-8 -*-

"""
    lunaport.plugg_views.dc
    ~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Dc - datacenter API resource.
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import jsonify, request, Response, url_for, session

from Base import BaseView
from .. dao.exceptions import StorageError
from .. dao.dc import RDBMS
from .. domain.dc import DcBuilder, DcAdaptor


class Dc(BaseView):
    str_params = [
        'name',
    ]
    int_params = [
        'page',
        'per_page',
    ]
    dao = RDBMS

    def get(self, dc_id):
        if dc_id is None:  # walk through all datacenters
            q = self.cmpl_query()
            try:
                dcs, per_page, next_page, prev_page = self.dao.get_many(**q)
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

            if not dcs:
                return Response(status=404)

            body = json.dumps(
                [DcAdaptor.to_resp(dc, jsonify=False) for dc in dcs])

            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
                'Link': self.cmpl_link_hdr(request, per_page, next_page,
                                           prev_page),
            }
            return Response(response=body, status=200,
                            headers=hdrs)
        else:  # try to get single *datacenter* entrie by id
            try:
                dc = self.dao.get_single(dc_id=dc_id)
            except StorageError as e:
                msg = {
                    'error_type': 'Storage call fails',
                    'error_text': str(e),
                }
                return jsonify(msg), 500

            if not dc:
                return Response(status=404)

            hdrs = {'Content-Type': 'application/json; charset=utf-8'}
            return Response(response=DcAdaptor.to_resp(dc), status=200,
                            headers=hdrs)

    def post(self):
        try:
            dc = DcBuilder.from_Flask_req(request, session)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            dc.id = self.dao.insert(dc)
            dc = self.dao.get_single(dc_id=dc.id)
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

        res_location = '{}{}'.format(url_for('dc'), dc.id)
        return Response(response=DcAdaptor.to_resp(dc), status=201,
                        headers={
                            'Location': res_location,
                            'Content-Type': 'application/json; charset=utf-8'
                        })

    def put(self):
        """ Update if exists ot create dc entrie.
        """
        try:
            dc = DcBuilder.from_Flask_req(request, session)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            dc = self.dao.update_or_create(dc)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        res_location = '{}{}'.format(url_for('dc'), dc.id)
        return Response(response=DcAdaptor.to_resp(dc), status=200,
                        headers={
                            'Location': res_location,
                            'Content-Type': 'application/json; charset=utf-8'
                        })

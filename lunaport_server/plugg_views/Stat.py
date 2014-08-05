# -*- encoding: utf-8 -*-
"""
    lunaport.plugg_views.stat
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Stat API resource.
    Ttest artefacts based statistic data.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint
import json

from flask import jsonify, request, Response
from flask.views import MethodView

from .. dao.exceptions import StorageError
from .. dao.stat import Stat as dao_stat
from .. domain.stat import StatBuilder


class Stat(MethodView):
    def get(self, test_id, ammo_tag):
        if ammo_tag is None:  # Retrieve avaliable tags for this test.
            try:
                s_tags = dao_stat.avail_ammo_tags(test_id)
            except StorageError as e:
                msg = {
                    'error_type': 'Storage call fails',
                    'error_text': str(e),
                }
                return jsonify(msg), 500
            if not s_tags:
                Response(status=404)

            body_json = json.dumps({'available_tags': s_tags})
            hdrs = {'Content-Type': 'application/json; charset=utf-8'}
            return Response(response=body_json, status=200,
                            headers=hdrs)

        # Particular stat by id.
        try:
            s = dao_stat.get(test_id, ammo_tag)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        if not s:
            return Response(status=404)

        hdrs = {'Content-Type': 'application/json; charset=utf-8'}
        return Response(response=s.as_json(), status=200,
                        headers=hdrs)

    def post(self, test_id, ammo_tag):

        try:
            stat = StatBuilder.from_Flask_req(request, test_id, ammo_tag)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            stat.id = dao_stat.insert(stat)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        return Response(response=stat.as_json(), status=201,
                        headers={
                            'Content-Type': 'application/json; charset=utf-8'
                        })

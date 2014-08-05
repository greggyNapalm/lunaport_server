# -*- encoding: utf-8 -*-
"""
    lunaport.plugg_views.chart
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Chart API resource.
    JSON based time series data for WEB UI charts.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import jsonify, request, Response
from flask.views import MethodView

from .. dao.exceptions import StorageError
from .. dao.chart import Chart as dao_chart
from .. domain.chart import ChartBuilder


class Chart(MethodView):
    def get(self, test_id, ammo_tag):
        try:
            c = dao_chart.get(test_id, ammo_tag)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        if not c:
            return Response(status=404)

        hdrs = {'Content-Type': 'application/json; charset=utf-8'}
        return Response(response=c.as_json(), status=200,
                        headers=hdrs)

    def post(self, test_id, ammo_tag):

        try:
            chart = ChartBuilder.from_Flask_req(request, test_id, ammo_tag)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            chart.id = dao_chart.insert(chart)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        return Response(response=chart.as_json(), status=201,
                        headers={
                            'Content-Type': 'application/json; charset=utf-8'
                        })

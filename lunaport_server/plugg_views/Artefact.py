# -*- encoding: utf-8 -*-
"""
    lunaport.plugg_views.artefact
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Artefact API resource.
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4)

from flask import jsonify, Response
from flask.views import MethodView

from .. dao.exceptions import StorageError
from .. dao.test import RDBMS as dao_test
from .. domain.art import ArtFabric


class Art(MethodView):
    def get(self, test_id):
        try:
            t = dao_test.get_by_id(test_id=test_id)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        if not t:
            msg = {
                'error_type': 'Missing resource',
                'error_text': 'No such test',
            }
            return jsonify(msg), 404

        try:
            arts = ArtFabric.from_test_entrie(t)
        except (TypeError, ValueError):
            msg = {
                'error_type': 'Missing resource',
                'error_text': 'No artefacts for such test',
            }
            return jsonify(msg), 404

        hdrs = {'Content-Type': 'application/json; charset=utf-8'}
        return Response(response=json.dumps(arts), status=200,
                        headers=hdrs)

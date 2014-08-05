# -*- encoding: utf-8 -*-
"""
    lunaport.plugg_views.artefact
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Artefact API resource.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4)

from flask import jsonify, request
from flask.views import MethodView

from .. domain.job import JobFabric
from .. dao.exceptions import StorageError


class Job(MethodView):

    def post(self):
        try:
            err = JobFabric.from_Flask_req(request)
        except (ValueError, AssertionError) as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500
        return jsonify({'error': err}), 201

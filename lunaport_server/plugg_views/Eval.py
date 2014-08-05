# -*- encoding: utf-8 -*-
"""
    lunaport.plugg_views.eval
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Evaluation API resource.
    Test evaluation result - JSON document with asserts names, params, results.
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import jsonify, request, Response, url_for

from Base import BaseView
from .. dao.exceptions import StorageError
from .. dao.eval import Eval as dao_eval
from .. domain.eval import EvalBuilder, EvalAdaptor


class Eval(BaseView):
    str_params = [
        'passed',
    ]
    int_params = [
        'test_id',
        'page',
        'per_page',
    ]

    def get(self, eval_id):
        if eval_id is None:  # walk through all evals.
            q = self.cmpl_query()
            try:
                evals, per_page, next_page, prev_page = dao_eval.get_many(**q)
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

            if not evals:
                return Response(status=404)

            body = json.dumps(
                [EvalAdaptor.to_resp(ev, jsonify=False) for ev in evals])

            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
                'Link': self.cmpl_link_hdr(request, per_page, next_page,
                                           prev_page),
            }
            return Response(response=body, status=200,
                            headers=hdrs)

        # Particular eval by id.
        try:
            t_eval = dao_eval.get(eval_id)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        if not t_eval:
            return Response(status=404)

        hdrs = {'Content-Type': 'application/json; charset=utf-8'}
        return Response(response=t_eval.as_json(), status=200,
                        headers=hdrs)

    def post(self, eval_id):
        try:
            t_eval = EvalBuilder.from_Flask_req(request)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            t_eval.id = dao_eval.insert(t_eval)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        hdrs = {
            'Content-Type': 'application/json; charset=utf-8',
            'Location': '{}{}'.format(url_for('eval'), t_eval.id),
        }

        return Response(response=t_eval.as_json(), status=201, headers=hdrs)

# -*- encoding: utf-8 -*-

"""
    lunaport.plugg_views.case
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Case API resource.
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import jsonify, request, Response, url_for, session

from Base import BaseView
from .. dao.exceptions import StorageError
from .. dao.case import RDBMS as dao_case
from .. domain.case import CaseBuilder


class Case(BaseView):
    @staticmethod
    def cmpl_query():
        str_params = [
            'case',
            'status',
            'env',
            'initiator',
            'issue',
            'load_src',
            'load_dst',
            'parent'
        ]
        int_params = [
            'page',
            'per_page',
        ]
        query = {}
        for p, v in request.args.items():
            if p in int_params:
                if not ((v.isdigit()) and (int(v) >= 0)):
                    raise ValueError('*{}* parameter malformed'.format(p))
                query.update({p: int(v)})

            if p in str_params:
                v_spltd = v.split(',')
                if len(v_spltd) > 1:  # list of values in HTTP param
                    query.update({p: v_spltd})
                else:  # singular string param
                    query.update({p: str(v)})
        return query

    @staticmethod
    def get_param(name):
        if name in ['page', 'per_page']:
            v = request.args.get(name)
            if not v:
                return None
            if not ((v.isdigit()) and (int(v) >= 0)):
                raise ValueError('*{}* parameter error'.format(name))
            return int(v)

    @staticmethod
    def get_names_butch(self):
            data = dao_case.get_names_butch()
            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
            }
            if not data:
                return Response(status=404)
            return Response(response=json.dumps(data), status=200,
                            headers=hdrs)

    def get(self, case_id):
        if case_id is None:  # walk through all cases
            if request.args.get('names_butch'):
                return self.get_names_butch(request)

            q = Case.cmpl_query()
            try:
                cases, per_page, next_page, prev_page = dao_case.get_many(**q)
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

            if not cases:
                return Response(status=404)

            body = json.dumps([c.as_dict(date_iso=True) for c in cases])
            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
                'Link': self.cmpl_link_hdr(request, per_page, next_page,
                                           prev_page),
            }
            return Response(response=body, status=200,
                            headers=hdrs)
        else:  # try to get single *case* entrie by id
            try:
                c = dao_case.get_by_id(case_id=case_id)
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

    def post(self):
        try:
            case = CaseBuilder.from_Flask_req(request, session)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            case.id = dao_case.insert(case)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        res_location = '{}{}'.format(url_for('case'), case.id)
        return Response(response=case.as_json(), status=201,
                        headers={
                            'Location': res_location,
                            'Content-Type': 'application/json; charset=utf-8'
                        })

    def patch(self, case_id):
        """
        Partially update of API resource.
        """
        diff = request.json
        if not diff:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': 'Can\'t deserialize json document',
            }
            return jsonify(msg), 422

        try:
            case = dao_case.update_by_id(case_id, diff)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        res_location = '{}{}'.format(url_for('case'), case.id)
        return Response(response=case.as_json(), status=200,
                        headers={
                            'Location': res_location,
                            'Content-Type': 'application/json; charset=utf-8'
                        })

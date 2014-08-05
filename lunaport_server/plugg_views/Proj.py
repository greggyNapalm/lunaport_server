# -*- encoding: utf-8 -*-

"""
    lunaport.plugg_views.proj
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Project API resource.
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import jsonify, request, Response, url_for

from Base import BaseView
from .. dao.exceptions import StorageError
from .. dao.proj import RDBMS as dao_proj
from .. domain.proj import ProjBuilder, ProjAdaptor


class Proj(BaseView):
    @staticmethod
    def get_names_butch(self):
            data = dao_proj.get_names_butch()
            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
            }
            if not data:
                return Response(status=404)
            return Response(response=json.dumps(data), status=200,
                            headers=hdrs)

    def get(self, proj_name):
        if proj_name is None:  # walk through all projects
            if request.args.get('names_butch'):
                return self.get_names_butch(request)

            q = self.cmpl_query()
            try:
                projs, per_page, next_page, prev_page = dao_proj.get_many(**q)
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

            if not projs:
                return Response(status=404)

            body = json.dumps(
                [ProjAdaptor.to_resp(p, jsonify=False) for p in projs])

            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
                'Link': self.cmpl_link_hdr(request, per_page, next_page,
                                           prev_page),
            }
            return Response(response=body, status=200,
                            headers=hdrs)
        else:  # try to get single *proj* entrie by name
            try:
                proj = dao_proj.get_by_name(proj_name=proj_name.lower())
            except StorageError as e:
                msg = {
                    'error_type': 'Storage call fails',
                    'error_text': str(e),
                }
                return jsonify(msg), 500

            if not proj:
                return Response(status=404)
            hdrs = {'Content-Type': 'application/json; charset=utf-8'}
            return Response(response=ProjAdaptor.to_resp(proj),
                            status=200, headers=hdrs)

    def post(self, proj_name):
        try:
            proj = ProjBuilder.from_Flask_req(request)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            proj.id = dao_proj.insert(proj)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        hdrs = {
            'Location': '{}{}'.format(url_for('proj'), proj.name),
            'Content-Type': 'application/json; charset=utf-8',
        }
        return Response(response=ProjAdaptor.to_resp(proj),
                        status=201, headers=hdrs)

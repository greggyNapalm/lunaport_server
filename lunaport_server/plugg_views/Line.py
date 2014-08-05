# -*- encoding: utf-8 -*-

"""
    lunaport.plugg_views.line
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Line(mean power line - district of datacenter) API resource.
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import jsonify, request, Response, url_for, session

from Base import BaseView
from .. dao.exceptions import StorageError
from .. dao.line import RDBMS
from .. domain.line import LineBuilder, LineAdaptor


class Line(BaseView):
    str_params = [
        'name',
    ]
    int_params = [
        'page',
        'per_page',
    ]
    dao = RDBMS

    def get(self, line_id):
        if line_id is None:  # walk through all lines
            q = self.cmpl_query()
            try:
                lines, per_page, next_page, prev_page = self.dao.get_many(**q)
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

            if not lines:
                return Response(status=404)

            body = json.dumps(
                [LineAdaptor.to_resp(l, jsonify=False) for l in lines])

            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
                'Link': self.cmpl_link_hdr(request, per_page, next_page,
                                           prev_page),
            }
            return Response(response=body, status=200,
                            headers=hdrs)
        else:  # try to get single *line* entrie by id
            try:
                line = self.dao.get_single(line_id=line_id)
            except StorageError as e:
                msg = {
                    'error_type': 'Storage call fails',
                    'error_text': str(e),
                }
                return jsonify(msg), 500

            if not line:
                return Response(status=404)

            hdrs = {'Content-Type': 'application/json; charset=utf-8'}
            return Response(response=LineAdaptor.to_resp(line), status=200,
                            headers=hdrs)

    def post(self):
        try:
            line = LineBuilder.from_Flask_req(request, session)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            line.id = self.dao.insert(line)
            line = self.dao.get_single(line_id=line.id)
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

        res_location = '{}{}'.format(url_for('line'), line.id)
        return Response(response=LineAdaptor.to_resp(line), status=201,
                        headers={
                            'Location': res_location,
                            'Content-Type': 'application/json; charset=utf-8'
                        })

    def put(self):
        """ Update if exists ot create Line entrie.
        """
        try:
            line = LineBuilder.from_Flask_req(request, session)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            line = self.dao.update_or_create(line)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        res_location = '{}{}'.format(url_for('line'), line.id)
        return Response(response=LineAdaptor.to_resp(line), status=200,
                        headers={
                            'Location': res_location,
                            'Content-Type': 'application/json; charset=utf-8'
                        })

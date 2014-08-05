# -*- encoding: utf-8 -*-

"""
    lunaport.plugg_views.path
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Path API resource.
    Path - trace path from load generator to target host
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import jsonify, request, Response, url_for, session

from Base import BaseView
from .. dao.exceptions import StorageError
from .. dao.path import RDBMS
from .. domain.path import PathBuilder, PathAdaptor


class Path(BaseView):
    str_params = [
        #'from_host',
        #'to_host',
    ]
    int_params = [
        'page',
        'per_page',
    ]
    dao = RDBMS

    def get(self, host_from, host_to):
        if host_from is None or host_to is None:  # plural entries
            q = self.cmpl_query()
            q.update({
                'host_from': host_from,
                'host_to': host_to,
            })
            try:
                paths, per_page, next_page, prev_page = self.dao.get_many(**q)
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

            if not paths:
                return Response(status=404)

            body = json.dumps(
                [PathAdaptor.to_resp(p, jsonify=False) for p in paths])

            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
                'Link': self.cmpl_link_hdr(request, per_page, next_page,
                                           prev_page),
            }
            return Response(response=body, status=200,
                            headers=hdrs)
        else:  # try to get single *path* entrie
            try:
                path = self.dao.get_single(host_from=host_from, host_to=host_to)
            except StorageError as e:
                msg = {
                    'error_type': 'Storage call fails',
                    'error_text': str(e),
                }
                return jsonify(msg), 500

            if not path:
                return Response(status=404)

            hdrs = {'Content-Type': 'application/json; charset=utf-8'}
            return Response(response=PathAdaptor.to_resp(path), status=200,
                            headers=hdrs)

    def post(self):
        path = PathBuilder.from_Flask_req(request, session)
        try:
            path = PathBuilder.from_Flask_req(request, session)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            host_from, host_to = self.dao.insert(path)
            #self.dao.insert(path)
            path = self.dao.get_single(host_from=host_from, host_to=host_to)
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

        res_location = '{}{}/{}'.format(url_for('path'), host_from, host_to)
        return Response(response=PathAdaptor.to_resp(path), status=201,
                        headers={
                            'Location': res_location,
                            'Content-Type': 'application/json; charset=utf-8'
                        })

    def patch(self, host_from, host_to):
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
            path = self.dao.update(diff, host_from=host_from, host_to=host_to)
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
            'Location': '{}{}/{}'.format(url_for('path'), host_from, host_to),
        }
        return Response(response=PathAdaptor.to_resp(path), status=200,
                        headers=hdrs)

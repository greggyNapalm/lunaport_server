# -*- encoding: utf-8 -*-
"""
    lunaport.plugg_views.host
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Host API resource.
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import jsonify, request, Response, url_for

from Base import BaseView
from .. dao.exceptions import StorageError
from .. dao.host import RDBMS
from .. domain.host import HostBuilder, HostAdaptor


class Host(BaseView):
    str_params = [
        'ip_addr',
        'dc',
        'line',
        'is_spec_tank',
        'is_tank',
    ]
    int_params = [
        'page',
        'per_page',
    ]
    dao = RDBMS

    @classmethod
    def get_names_butch(cls):
            data = cls.dao.get_names_butch()
            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
            }
            if not data:
                return Response(status=404)
            return Response(response=json.dumps(data), status=200,
                            headers=hdrs)

    def get(self, host_fqdn):
        if request.args.get('names_butch'):
            return self.get_names_butch()

        if host_fqdn is None:  # walk through all hosts 
            q = self.cmpl_query()
            try:
                hosts, per_page, next_page, prev_page = self.dao.get_many(**q)
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
                return jsonify(msg), 422

            if not hosts:
                return Response(status=404)

            body = json.dumps(
                [HostAdaptor.to_resp(h, jsonify=False) for h in hosts])

            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
                'Link': self.cmpl_link_hdr(request, per_page, next_page,
                                           prev_page),
            }
            return Response(response=body, status=200,
                            headers=hdrs)
        else:  # try to get single *host* entrie by fqdn
            try:
                host = self.dao.get_by_fqdn(fqdn=host_fqdn)
            except StorageError as e:
                msg = {
                    'error_type': 'Storage call fails',
                    'error_text': str(e),
                }
                return jsonify(msg), 500
            if not host:
                return Response(status=404)

            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
            }
            return Response(response=HostAdaptor.to_json(host), status=200,
                            headers=hdrs)

    def post(self, host_fqdn):
        try:
            host = HostBuilder.from_Flask_req(request)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            host.id = self.dao.insert(host)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        hdrs = {
            'Content-Type': 'application/json; charset=utf-8',
            'Location': '{}{}'.format(url_for('host'), host.fqdn),
        }
        return Response(response=HostAdaptor.to_resp(host), status=200,
                        headers=hdrs)

    def patch(self, host_fqdn):
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
            host = self.dao.update_by_name(host_fqdn, diff)
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
            'Location': '{}{}'.format(url_for('host'), host.fqdn),
        }
        return Response(response=HostAdaptor.to_resp(host), status=200,
                        headers=hdrs)

    def put(self, host_fqdn):
        """ Update if exists ot create host entrie.
        """
        try:
            host = HostBuilder.from_Flask_req(request)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            host = self.dao.update_or_create(host)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500
        hdrs = {
            'Content-Type': 'application/json; charset=utf-8',
            'Location': '{}{}'.format(url_for('host'), host.fqdn),
        }
        return Response(response=HostAdaptor.to_resp(host), status=200,
                        headers=hdrs)

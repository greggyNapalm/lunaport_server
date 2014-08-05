# -*- encoding: utf-8 -*-

"""
    lunaport.plugg_views.issue
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Issue API resource.
"""

import json
import urllib
import pprint
pp = pprint.PrettyPrinter(indent=4)

from flask import jsonify, request, Response, url_for
from flask.views import MethodView

from .. dao.exceptions import StorageError
from .. dao.issue import RDBMS as dao_issue
from .. domain.issue import IssueBuilder


class Issue(MethodView):
    @staticmethod
    def cmpl_query():
        str_params = [
            'title',
            'descr',
            'reporter',
            'assignee',
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
    def cmpl_location_hdr(per_page, page):
        url_cuted = request.url.split('?')[0]
        params = dict(request.args.items())
        params.update({
            'per_page': per_page,
            'page': page,
        })
        return '{}?{}'.format(url_cuted, urllib.urlencode(params))

    @staticmethod
    def get_names_butch(self):
            data = dao_issue.get_names_butch()
            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
            }
            if not data:
                return Response(status=404)
            return Response(response=json.dumps(data), status=200,
                            headers=hdrs)

    def get(self, issue_name):
        if issue_name is None:  # walk through all issues
            if request.args.get('names_butch'):
                return self.get_names_butch(request)
            q = self.cmpl_query()
            try:
                issues, per_page, page = dao_issue.get_many(**q)
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

            if not issues:
                return Response(status=404)

            body = json.dumps([i.as_dict(date_iso=True) for i in issues])
            next_page_url = Issue.cmpl_location_hdr(per_page, page)
            hdrs = {
                'Link': '<{}>; rel="next"'.format(next_page_url),
                'Content-Type': 'application/json; charset=utf-8'
            }
            return Response(response=body, status=200,
                            headers=hdrs)
        else:  # try to get single *issue* entrie by name
            try:
                issue = dao_issue.get_by_name(issue_name=issue_name.lower())
            except StorageError as e:
                msg = {
                    'error_type': 'Storage call fails',
                    'error_text': str(e),
                }
                return jsonify(msg), 500

            if not issue:
                return Response(status=404)

            hdrs = {'Content-Type': 'application/json; charset=utf-8'}
            return Response(response=issue.as_json(), status=200, headers=hdrs)

    def post(self, issue_name):
        try:
            issue = IssueBuilder.from_Flask_req(request)
        except ValueError as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        try:
            issue.id = dao_issue.insert(issue)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        hdrs = {
            'Location': '{}{}'.format(url_for('issue'), issue.name),
            'Content-Type': 'application/json; charset=utf-8',
        }
        return Response(response=issue.as_json(), status=201, headers=hdrs)

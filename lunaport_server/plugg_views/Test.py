# -*- encoding: utf-8 -*-

"""
    lunaport.plugg_views.test
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Test API resource.
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import jsonify, request, Response, redirect, url_for, session
from flask.views import MethodView

from Base import BaseView
from .. dao.exceptions import StorageError
from .. dao.case import RDBMS as rdbms_case
from .. dao.test import SideEffect, RDBMS
from .. domain.test import TestBuilder, TestAdaptor, fetch_luanapark_repr,\
    fetch_tests_offline
from resources import badge


class Test(BaseView):
    str_params = [
        'case',
        'status',
        'env',
        'initiator',
        'issue',
        'load_src',
        'load_dst',
        'parent',
        'ammo'
    ]
    int_params = [
        'page',
        'per_page',
    ]
    dao = SideEffect(RDBMS)

    def get(self, test_id):
        if test_id is None:  # walk through all tests
            q = self.cmpl_query()
            try:
                tests, per_page, next_page, prev_page = self.dao.get_many(**q)
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

            if not tests:
                return Response(status=404)

            body = json.dumps(
                [TestAdaptor.to_resp(t, jsonify=False) for t in tests])

            hdrs = {
                'Content-Type': 'application/json; charset=utf-8',
                'Link': self.cmpl_link_hdr(request, per_page, next_page,
                                           prev_page),
            }
            return Response(response=body, status=200,
                            headers=hdrs)
        else:  # try to get single *test* entrie by id
            try:
                t = self.dao.get_by_id(test_id=test_id)
            except StorageError as e:
                msg = {
                    'error_type': 'Storage call fails',
                    'error_text': str(e),
                }
                return jsonify(msg), 500

            if not t:
                return Response(status=404)

            hdrs = {'Content-Type': 'application/json; charset=utf-8'}
            return Response(response=t.as_json(), status=200,
                            headers=hdrs)

    def insert_test(self, test, autocomplete):
        try:
            test.id = self.dao.insert(test)
            return test, None
        except StorageError as e:
            succ_added = False
            if autocomplete:
                try:
                    succ_added = self.autocomplete(
                        getattr(e, 'missing_resource_type', None),
                        getattr(e, 'missing_resource_value', None))
                except ValueError as e:
                        return None, e

            if succ_added:
                return self.insert_test(test, autocomplete)
            return None, e

    def post(self):
        try:
            test, autocomplete = TestBuilder.from_Flask_req(request, session)
        except (ValueError, AssertionError) as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        test, err = self.insert_test(test, autocomplete)
        if err:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(err),
            }
            return jsonify(msg), 500

        hdrs = {
            'Content-Type': 'application/json; charset=utf-8',
            'Location': '{}{}'.format(url_for('test'), test.id),
        }
        return Response(response=TestAdaptor.to_resp(test), status=201,
                        headers=hdrs)

    def patch(self, test_id):
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
            test = self.dao.update_by_id(test_id, diff)
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
            'Location': '{}{}'.format(url_for('test'), test.id),
        }
        return Response(response=TestAdaptor.to_resp(test), status=200,
                        headers=hdrs)


class LunaparkTest(MethodView):
    """
    Redirects to test resource(if exists).
    """
    dao = SideEffect(RDBMS)

    def get(self, luna_test_id):
        try:
            t = self.dao.get_by_id(lunapark_id=luna_test_id)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        if t:
            return redirect('{}{}'.format(url_for('test'), t.id))

        try:
            t = fetch_luanapark_repr(luna_test_id)
        except ValueError as e:
            msg = {
                'error_text': str(e),
            }
            return jsonify(msg), 598

        if not t:
            msg = {'offline_lunapark_tests': fetch_tests_offline()}
            return jsonify(msg), 404

        hdrs = {'Content-Type': 'application/json; charset=utf-8'}
        return Response(response=json.dumps(t), status=200,
                        headers=hdrs)


class RootTest(MethodView):
    """
    Handle case urls like status and badge,
    which refers to case's root test.
    """
    dao = SideEffect(RDBMS)

    def get_badge(self, c, badge_name):
        """
        Generate SVG badge image according to last finished test resolution.

        Args:
            c - case instance.
        """
        try:
            q = {
                'case': c.name,
                'status': 'done',
            }
            t = RDBMS.get_many(**q)[0]
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        if not t:
            msg = {
                'error_type': 'malformed case instance',
                'error_text': 'There is no any tests with status *done* in such case',
            }
            return jsonify(msg), 422

        badge_key = str(t[0].resolution)
        #if 'marked' in dict(request.args.items()).keys():
        if 'marked' in badge_name:
            badge_key += '_marked'
        return Response(response=badge[badge_key], status=200,
                        headers={'Content-Type': 'image/svg+xml'})

    def start_root_fot_case(self, root_test_id, initiator=None):
        """
        Launch new load test via copying root test cfg.
        Responce with redirect to new tests page.

        Args:
            root_test_id - int. 
        """
        if not root_test_id:
            msg = {
                'error_type': 'malformed case instance',
                'error_text': 'case should have not null value for *root_test_id* attribute',
            }
            return jsonify(msg), 422

        try:
            t = RDBMS.get_by_id(test_id=root_test_id)
        except StorageError as e:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        # To mock POST requsts with JSON body
        class DummyRequest(dict):
            pass
        r = DummyRequest()
        r.mimetype = 'application/json'
        msg_rv = r.json = t.generator_cfg
        msg_rv['env'] = 'luna-tank-api-force'
        if initiator:
            msg_rv['lunaport']['initiator'] = initiator
        test_method_view = Test()

        try:
            test_inst = TestBuilder.launch(r, session, msg_rv)
        except (ValueError, AssertionError) as e:
            msg = {
                'error_type': 'Malformed body attributes',
                'error_text': str(e),
            }
            return jsonify(msg), 422

        test_inst, err = test_method_view.insert_test(test_inst, False)
        if err:
            msg = {
                'error_type': 'Storage call fails',
                'error_text': str(err),
            }
            return jsonify(msg), 500

        ui_test_url = '{}tests/{}/all'.format(request.url_root, test_inst.id)
        return redirect(ui_test_url)

    def get(self, case_id, action, img_name):
        try:
            c = rdbms_case.get_by_id(case_id=case_id)
        except StorageError as e:
            msg = {
                'error_type': 'Wrong case id',
                'error_text': 'case fetch failed:' + str(e),
            }
            return jsonify(msg), 422

        if not c:
            msg = {
                'error_type': 'Wrong case id',
                'error_text': 'case not found',
            }
            return jsonify(msg), 404

        if action == 'oneshot':
            root_test_id = getattr(c, 'root_test_id')
            return self.start_root_fot_case(root_test_id)
        elif action.startswith('badge'):
            return self.get_badge(c, action)
        else:
            msg = {
                'error_type': 'malformed request path',
                'error_text': 'action:{} not supported'.format(action),
            }
            return jsonify(msg), 422

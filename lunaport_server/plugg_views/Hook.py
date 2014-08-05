# -*- encoding: utf-8 -*-

"""
    lunaport.plugg_views.hook
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for hook resource.
    Allow to retrieve available hooks.
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import jsonify, Response, request

from ..wsgi import app
from Base import BaseView
from .. dao.exceptions import StorageError
from .. dao.hook import RDBMS
from .. domain.hook import HookAdaptor, HookProcessor 
from .. helpers import get_logger 


class Hook(BaseView):
    dao = RDBMS

    def get(self):
        try:
            hooks = self.dao.get_all()
        except StorageError as e:
            msg = {
                'error_type': 'storage call fails',
                'error_text': str(e),
            }
            return jsonify(msg), 500
        except ValueError as e:
            msg = {
                'error_type': 'business logic layer error',
                'error_text': str(e),
            }
            return jsonify(msg), 500

        if not hooks:
            return Response(status=404)

        body = json.dumps(
            [HookAdaptor.to_resp(h, jsonify=False) for h in hooks])

        hdrs = {
            'content-type': 'application/json; charset=utf-8',
        }
        return Response(response=body, status=200,
                        headers=hdrs)


class GithubHandler(BaseView):
    def post(self):
        if request.mimetype == 'multipart/form-data':
            msg_rv = request.form

        elif request.mimetype == 'application/json':
            msg_rv = request.json
        else:
            raise ValueError('Unsupported mime type')
        print '-' * 80
        print 'Github hook catched'
        print '-' * 80
        pp(msg_rv)
        return jsonify({'hook': 'catched'}), 500


class someHandler(BaseView):
    ext = {
        'hook_handler': 'some'
    }
    logger = get_logger(app.config.get('LOGGING'), **ext)
    def post(self):
        """
        some hook request body example:
        {   u'author': u'gkomissarov',
            u'branch': u'testing',
            u'comment': u'',
            u'modifier': u'le087',
            u'new_status': u'done',
            u'old_status': u'restarted',
            u'packages': [   {   u'package': u'lunaport-check-c-web-hook',
                                 u'version': u'0.0.11'}],
            u'task': u'CS-401500'}
        """
        if request.mimetype == 'multipart/form-data':
            msg_rv = request.form

        elif request.mimetype == 'application/json':
            msg_rv = request.json
        else:
            self.logger.error('Failed to deserialize hooks body.')
            raise ValueError('Unsupported mime type')
    
        hp = HookProcessor(self.logger)
        hp.handle('some', msg_rv)
        return jsonify({'hook': 'catched'}), 200 

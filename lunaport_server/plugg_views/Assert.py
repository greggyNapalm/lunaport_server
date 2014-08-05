# -*- encoding: utf-8 -*-
"""
    lunaport.plugg_views.assert
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view for Assert API resource. List of available for
    oracle(evaluation).
"""

import json
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import Response
from flask.views import MethodView

from lunaport_worker.tasks import t_assert


class Assert(MethodView):

    def get(self):
        hdrs = {'Content-Type': 'application/json; charset=utf-8'}

        def adapt_assert((k, v)):
            return {
                'args': v['args'],
                'docstr': v['docstr'],
                'name': k,
            }
        asrts = map(adapt_assert, t_assert.get_asserts().iteritems())
        return Response(response=json.dumps(asrts),
                        status=200, headers=hdrs)

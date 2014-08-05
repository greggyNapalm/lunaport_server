# -*- encoding: utf-8 -*-
"""
    lunaport.plugg_views.healthstatus
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Class-based view to show service HealthStatus.
"""

#import urllib
import os
import datetime
import json
import pkg_resources
import commands
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask.views import MethodView
from flask import Response
import psutil

from lunaport_worker.tasks.utils import celery


class Status(MethodView):
    def get(self):
        modules = [
            {
                'name': 'lunaport_worker',
                'deb': 'python-lunaport-worker',
                'changelog_lnk': 'https://github.domain.ru/gkomissarov/lunaport_worker/blob/master/debian/changelog'
            },
            {
                'name': 'lunaport_server',
                'deb': 'python-lunaport-server',
                'changelog_lnk': 'https://github.domain.ru/gkomissarov/lunaport_server/blob/master/debian/changelog',
            },
            {
                'name': 'lunaport_client',
                'deb': 'python-lunaport-client',
                'changelog_lnk': 'https://github.domain.ru/gkomissarov/lunaport_client/blob/master/debian/changelog',
            },
            {
                'name': 'lunapark_client',
                'deb': 'python-lunapark-client',
                'changelog_lnk': 'https://github.domain.ru/gkomissarov/lunapark_client/blob/master/debian/changelog',
            },
            {
                'name': 'lunaport-web-ui',
                'deb': 'lunaport-web-ui',
                'changelog_lnk': 'https://github.domain.ru/gkomissarov/lunaport_web_ui/blob/master/debian/changelog'
            },

        ]

        py_ver = lambda module: pkg_resources.get_distribution(module).version
        deb_ver = lambda pkg: commands.getstatusoutput(
            "dpkg -s {} 2>/dev/null | grep '^Version' | awk '{{print $2}}'".format(pkg))[1]

        for m in modules:
            m['py_version'] = None 
            try:
                m['py_version'] = py_ver(m['name'])
            except Exception:
                pass
            m['deb_version'] = deb_ver(m['deb'])

        p = psutil.Process(os.getpid())

        hdrs = {'Content-Type': 'application/json; charset=utf-8'}
        msg = {
            'modules': modules,
            'celery': {
                'ping': celery.control.inspect().ping(),
            },
            'uptime': {
                'started_at': datetime.datetime.utcfromtimestamp(p.create_time).isoformat()
            }
        }
        return Response(response=json.dumps(msg), status=200,
                        headers=hdrs)

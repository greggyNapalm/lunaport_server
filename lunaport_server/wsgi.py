#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
lunaport_server.wgi
~~~~~~~~~~~~~~~~~~~

Describes  WSGI application.
"""

import os

from flask import Flask
from werkzeug.contrib.fixers import ProxyFix
from flask.ext.sqlalchemy import SQLAlchemy
from raven.contrib.flask import Sentry

app = Flask(__name__)
app.config.from_envvar('LUNAPORT_CFG')
app.wsgi_app = ProxyFix(app.wsgi_app)  # Fix for old proxyes
db = SQLAlchemy(app)

if os.environ.get('LUNAPORT_ENV') == 'production':
    sentry = Sentry(app, dsn=app.config.get('SENTRY_DSN'))
    sentry.init_app(app)

from plugg_views import User, Issue, Test, Host, Stat, Chart, Eval, Case, \
    Artefact, Job, Assert, Proj, Notification, Token, Ammo, Dc, Line, \
    HealthStatus, Hook, HookRegistration 
from helpers import auth_required

user_ident = auth_required(User.UserIdent.as_view('user_ident'))
user_view = auth_required(User.User.as_view('user'))
test_view = auth_required(Test.Test.as_view('test'))
case_view = auth_required(Case.Case.as_view('case'))
host_view = auth_required(Host.Host.as_view('host'))
issue_view = auth_required(Issue.Issue.as_view('issue'))
proj_view = auth_required(Proj.Proj.as_view('proj'))
stat_view = auth_required(Stat.Stat.as_view('stat'))
chart_view = auth_required(Chart.Chart.as_view('chart'))
eval_view = auth_required(Eval.Eval.as_view('eval'))
arts_view = auth_required(Artefact.Art.as_view('artefact'))
job_view = auth_required(Job.Job.as_view('job'))
assert_view = auth_required(Assert.Assert.as_view('assert'))
notifcn_view = auth_required(Notification.Notifcn.as_view('notification'))
token_view = auth_required(Token.Token.as_view('token'))
health_status_view = HealthStatus.Status.as_view('healthstatus')
ammo_view = auth_required(Ammo.Ammo.as_view('ammo'))
dc_view = auth_required(Dc.Dc.as_view('dc'))
line_view = auth_required(Line.Line.as_view('line'))
root_test_view = auth_required(Test.RootTest.as_view('root_test'))
hook_view = auth_required(Hook.Hook.as_view('hook'))
hook_registration_view = auth_required(HookRegistration.HookRegistration.as_view('hook_registration'))
github_hook_handler = Hook.GithubHandler.as_view('github_hook_handler')
conductor_hook_handler = Hook.ConductorHandler.as_view('conductor_hook_handler')

app.add_url_rule('/api/v1.0/userident/', view_func=user_ident, methods=['GET'])
app.add_url_rule('/api/v1.0/user/', defaults={'login': None}, view_func=user_view, methods=['GET'])
app.add_url_rule('/api/v1.0/user/', view_func=user_view, methods=['POST'])
app.add_url_rule('/api/v1.0/user/<login>', view_func=user_view, methods=['GET', 'PATCH'])

app.add_url_rule('/api/v1.0/tests/', defaults={'test_id': None}, view_func=test_view, methods=['GET'])
app.add_url_rule('/api/v1.0/tests/', view_func=test_view, methods=['POST'])
app.add_url_rule('/api/v1.0/tests/<int:test_id>', view_func=test_view, methods=['GET', 'PATCH', 'DELETE'])
app.add_url_rule('/api/v1.0/tests/luna/<luna_test_id>', view_func=Test.LunaparkTest.as_view('luna_test'), methods=['GET'])

app.add_url_rule('/api/v1.0/tests/<int:test_id>/stat/', defaults={'ammo_tag': None}, view_func=stat_view, methods=['GET'])
app.add_url_rule('/api/v1.0/tests/<int:test_id>/stat/<ammo_tag>', view_func=stat_view, methods=['GET', 'POST'])
app.add_url_rule('/api/v1.0/tests/<int:test_id>/chart/<ammo_tag>', view_func=chart_view, methods=['GET', 'POST'])
app.add_url_rule('/api/v1.0/tests/<int:test_id>/arts', view_func=arts_view, methods=['GET'])

app.add_url_rule('/api/v1.0/case/', defaults={'case_id': None}, view_func=case_view, methods=['GET'])
app.add_url_rule('/api/v1.0/case/', view_func=case_view, methods=['POST'])
app.add_url_rule('/api/v1.0/case/<int:case_id>', view_func=case_view, methods=['GET', 'PATCH', 'DELETE'])
app.add_url_rule('/api/v1.0/case/<int:case_id>/badge/<img_name>', defaults={'action': 'badge'}, view_func=root_test_view, methods=['GET'])
app.add_url_rule('/api/v1.0/case/<int:case_id>/badge-marked/<img_name>', defaults={'action': 'badge-marked'}, view_func=root_test_view, methods=['GET'])
app.add_url_rule('/api/v1.0/case/<int:case_id>/oneshot', defaults={'action': 'oneshot', 'img_name': None}, view_func=root_test_view, methods=['GET'])

app.add_url_rule('/api/v1.0/host/', defaults={'host_fqdn': None}, view_func=host_view, methods=['GET', 'POST', 'PUT'])
app.add_url_rule('/api/v1.0/host/<host_fqdn>', view_func=host_view, methods=['GET', 'PATCH'])

app.add_url_rule('/api/v1.0/issue/', defaults={'issue_name': None}, view_func=issue_view, methods=['GET', 'POST'])
app.add_url_rule('/api/v1.0/issue/<issue_name>', view_func=issue_view, methods=['GET', 'PATCH', 'DELETE'])

app.add_url_rule('/api/v1.0/proj/', defaults={'proj_name': None}, view_func=proj_view, methods=['GET', 'POST'])
app.add_url_rule('/api/v1.0/proj/<proj_name>', view_func=proj_view, methods=['GET', 'PATCH', 'DELETE'])

app.add_url_rule('/api/v1.0/eval/', defaults={'eval_id': None}, view_func=eval_view, methods=['POST', 'GET'])
app.add_url_rule('/api/v1.0/eval/<int:eval_id>', view_func=eval_view, methods=['GET'])

app.add_url_rule('/api/v1.0/job/', view_func=job_view, methods=['POST'])
app.add_url_rule('/api/v1.0/asserts/', view_func=assert_view, methods=['GET'])

app.add_url_rule('/api/v1.0/notifications/', defaults={'case_name': None, 'user_login': None}, view_func=notifcn_view, methods=['GET', 'POST'])
app.add_url_rule('/api/v1.0/notifications/<case_name>/<user_login>', view_func=notifcn_view, methods=['GET', 'PATCH'])

app.add_url_rule('/api/v1.0/token/', view_func=token_view, methods=['GET', 'POST'])
app.add_url_rule('/api/v1.0/token/<token_id>', view_func=token_view, methods=['DELETE'])

app.add_url_rule('/api/v1.0/ammo/', defaults={'ammo_id': None}, view_func=ammo_view, methods=['GET'])
app.add_url_rule('/api/v1.0/ammo/', view_func=ammo_view, methods=['POST'])
app.add_url_rule('/api/v1.0/ammo/<int:ammo_id>', view_func=ammo_view, methods=['GET', 'PATCH', 'DELETE'])

app.add_url_rule('/api/v1.0/dc/', defaults={'dc_id': None}, view_func=dc_view, methods=['GET'])
app.add_url_rule('/api/v1.0/dc/', view_func=dc_view, methods=['POST', 'PUT'])
app.add_url_rule('/api/v1.0/dc/<int:dc_id>', view_func=dc_view, methods=['GET', ])

app.add_url_rule('/api/v1.0/line/', defaults={'line_id': None}, view_func=line_view, methods=['GET'])
app.add_url_rule('/api/v1.0/line/', view_func=line_view, methods=['POST', 'PUT'])
app.add_url_rule('/api/v1.0/line/<int:line_id>', view_func=line_view, methods=['GET', ])

app.add_url_rule('/api/v1.0/status/', view_func=health_status_view, methods=['GET'])

app.add_url_rule('/api/v1.0/hooks/', view_func=hook_view, methods=['GET'])
app.add_url_rule('/api/v1.0/hooks/registration/', defaults={'hook_registration_id': None}, view_func=hook_registration_view, methods=['GET'])
app.add_url_rule('/api/v1.0/hooks/registration/', view_func=hook_registration_view, methods=['POST'])
app.add_url_rule('/api/v1.0/hooks/registration/<int:hook_registration_id>', view_func=hook_registration_view, methods=['GET', 'PATCH', 'DELETE'])

app.add_url_rule('/api/v1.0/hooks/github', view_func=github_hook_handler, methods=['POST'])
app.add_url_rule('/api/v1.0/hooks/conductor', view_func=conductor_hook_handler, methods=['POST'])


#app.add_url_rule('/api/v1.0/hooks/emitter/conductor', view_func=hooks_conductor_view, methods=['POST'])
#app.add_url_rule('/api/v1.0/hooks/', view_func=registered_hooks_view, methods=['GET', 'POST'])

#app.add_url_rule('/api/v1.0/hooks/', defaults={'hook_id': None}, view_func=registered_hook_view, methods=['GET'])
#app.add_url_rule('/api/v1.0/hooks/', view_func=registered_hook_view, methods=['POST'])
#app.add_url_rule('/api/v1.0/hooks/<int:hook_id>', view_func=registered_hook_view, methods=['GET', 'PATCH', 'DELETE'])

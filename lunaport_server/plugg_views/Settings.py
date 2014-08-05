# -*- encoding: utf-8 -*-

"""
dash_server.plugg_views.settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Describes WSGI application.
"""


from flask import session, jsonify
from flask.views import MethodView

from .. import dao


class Settings(MethodView):
    def get(self):
        login = session.get('login', None)
        if login:
            usr = dao.User(login).get()
            return jsonify(usr.get_settings()), 200

        return jsonify({'msg': 'No settings for robots.'}), 404

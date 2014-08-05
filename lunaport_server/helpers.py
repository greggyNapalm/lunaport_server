# -*- encoding: utf-8 -*-

"""
    lunaport.helpers
    ~~~~~~~~~~~~~~~~

    Common for whole app useful functions.
"""
import os
import imp
import socket
from functools import wraps
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from flask import request, session

#from dao.user import RDBMS as dao_user
from dao.user import SideEffect, RDBMS
from dao import token as dao_token
from domain import user as domain_usr
from ya.helpers import auth as external_auth
from lunaport_worker.helpers import compose_logger

dao_user = SideEffect(RDBMS)


def auth_required(f):
    ''' This decorator can be used on any view which should only be visited by
        authenticated clients. Two type of auth supported:
        * external by auth service provider.
        * internal by tokens(HTTP request param).
    '''
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            login = external_auth(request)
        except:
            login = None

        if login:
            if not dao_user.does_exist(login):
                u = domain_usr.UserBuilder.from_login(login)
                dao_user.insert(u)

            session['login'] = login
            return f(*args, **kwargs)

        auth = request.authorization
        if auth:
            token_owner = dao_token.Token.meet(auth.username, auth.password)
            if token_owner:
                session['login'] = token_owner
                return f(*args, **kwargs)

        return 'Not authenticated', 401
    return decorated


def get_app_cfg(envvar='LUNAPORT_CFG'):
    cfg = {}
    cfg_path = os.environ[envvar]
    d = imp.new_module('app_config')
    d.__file__ = cfg_path
    execfile(cfg_path, d.__dict__)
    for key in dir(d):
        if key.isupper():
            cfg[key] = getattr(d, key)
    return cfg


def validate_net_addr(addr):
    """ Check is provided str a valid ipv4/ipv6 addr or not.
    """
    try:
        socket.inet_pton(socket.AF_INET, addr)
        return 4
    except socket.error:
        pass

    try:
        socket.inet_pton(socket.AF_INET6, addr)
        return 6
    except socket.error:
        pass

    return None


def get_logger(logger_cfg, **kw):
    kw.update({
        'env': os.environ.get('LUNAPORT_ENV', 'lunaport-dev')
    })
    return compose_logger(logger_cfg, extra=kw)

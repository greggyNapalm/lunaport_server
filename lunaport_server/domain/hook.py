# -*- encoding: utf-8 -*-

"""
    lunaport.domain.hook
    ~~~~~~~~~~~~~~~~~~~~
    hook - like a connection type.
"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from base import BaseFactory, BaseAdaptor, BaseEntrie
from .. dao.hook_registration import RDBMS as dao_hook_registration
from .. dao.case import RDBMS as dao_case
from .. plugg_views.Test import RootTest


class Hook(BaseEntrie):
    """
    Hook instance.
    """
    attr_required = [
        'id',
        'name',
        'descr',
        'cfg_example'
    ]
    attr_optional = []


class HookAdaptor(BaseAdaptor):
    pass


class HookBuilder(BaseFactory):
    target_struct = Hook


class BasicHookCatcher(object):
    """
    All inheritors will be used as hook catchers/handlers.
    """
    class __metaclass__(type):
        __inheritors__ = []

        def __new__(meta, name, bases, dct):
            klass = type.__new__(meta, name, bases, dct)
            for base in klass.mro()[1:-1]:
                meta.__inheritors__.append(klass)
            return klass

    @classmethod
    def fillter_registration(cls, reg_cfg, msg):
        raise NotImplemented()


class ConductorHookCatcher(BasicHookCatcher):
    name = 'conductor'

    @staticmethod
    def is_registered(reg, msg):
        if msg.get('branch') != reg.cfg.get('branch'):
            return False

        pkgs = [p['package'] in reg.cfg.get('packages') for p in msg.get('packages')]
        if not any(pkgs):
            return False

        comment_contains = reg.cfg.get('comment_contains')
        if comment_contains:
            if not comment_contains in msg.get('comment'):
                return False
        return True


class GithubHookCatcher(BasicHookCatcher):
    name = 'github'

    @classmethod
    def __repr__(cls):
        return '<{} hook catcher>'.format(cls.name)

    @classmethod
    def __str__(cls):
        return '<{} hook catcher>'.format(cls.name)

    @classmethod
    def fillter_registration(cls, reg_cfg, msg):
        return True


class HookProcessor(object):
    """
    Handle hook request from 3rd party service.
    """
    _handlers = {h.name: h for h in BasicHookCatcher.__inheritors__}

    def __init__(self, logger):
        self.logger = logger

    def luanch_test(self, case_id, initiator):
        c = dao_case.get_by_id(case_id=case_id)
        if not c:
            err_msg = 'Case not found case_id:{}'.format(case_id)
            self.logger.error(err_msg)
            raise ValueError(err_msg)
        root_test_id = getattr(c, 'root_test_id')
        view_class = RootTest()
        rv = view_class.start_root_fot_case(root_test_id, initiator=initiator)
        try:
            resp = rv[0]
        except TypeError:
            resp = rv
        self.logger.info(
            'Reacting on hook, test launched, case_id:{}, resp:{}'.format(
                case_id, getattr(resp, 'response')))

    def handle(self, hook_name, msg):
        if hook_name not in self._handlers:
            err_msg = 'Hook with name:{} not supported'.format(hook_name)
            self.logger.error(err_msg)
            raise ValueError(err_msg)
        self.catcher = self._handlers[hook_name]

        self.registrations = self.get_registrations(hook_name)
        if not self.registrations:
            err_msg = 'No registration found for hook:{}'.format(hook_name)
            self.logger.warning(err_msg)
            return None

        self.suitable_regs = filter(lambda r: self.catcher.is_registered(r, msg), self.registrations)
        if not self.suitable_regs:
            err_msg = 'No suitable registration found for hook:{} and msg:{}'.format(hook_name, msg)
            self.logger.error(err_msg)
            return None

        for r in self.suitable_regs:
            self.luanch_test(r.case_id, msg['author'])

    @staticmethod
    def get_registrations(hook_name):
        return dao_hook_registration.get_many(hook_name=hook_name,
                                              is_enabled='True')[0]

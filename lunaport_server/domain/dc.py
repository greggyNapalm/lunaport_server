# -*- encoding: utf-8 -*-

"""
    lunaport.domain.dc
    ~~~~~~~~~~~~~~~~~~
    Datacenter related business logic
"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from base import BaseFactory, BaseAdaptor, BaseEntrie


class Dc(BaseEntrie):
    """
    Datacenter - describes physical server placement.
    Contains multiple lines(power line).
    """
    attr_required = [
        'name',
    ]
    attr_optional = [
        'id',
    ]


class DcAdaptor(BaseAdaptor):
    __just_inherit = True


class DcBuilder(BaseFactory):
    """ Datacenter instance static fabric.
    """
    target_struct = Dc
    req_attr_allowed = [
        'name',
    ]
    req_attr_allowed_set = set(req_attr_allowed)

    @classmethod
    def from_Flask_req(cls, r, session):
        """ Creates class instance from Flask request object.
        Args:
            r: Flask request object.
            session: Flask session object.

        Returns:
            Ammo class instance.
        """
        msg_rvd = cls.parse_flask_req(r, session)
        return Dc(**msg_rvd)

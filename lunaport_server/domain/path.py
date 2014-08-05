# -*- encoding: utf-8 -*-

"""
    lunaport.domain.path
    ~~~~~~~~~~~~~~~~~~~~
    Path related business logic
"""
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from base import BaseFactory, BaseAdaptor, BaseEntrie


class Path(BaseEntrie):
    """
    Line(power line or queue) - district of datacenter.
    """
    attr_required = [
        'host_from',
        'host_to',
        'num',
        'hops'
    ]
    attr_optional = []
        #'dc',
    #]


class PathAdaptor(BaseAdaptor):
    __just_inherit = True


class PathBuilder(BaseFactory):
    """ Line instance static fabric.
    """
    target_struct = Path
    req_attr_allowed = [
        'host_from',
        'host_to',
        'num',
        'hops'
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
        return Path(**msg_rvd)

    @classmethod
    def from_row(cls, **row):
        """Creates class instance from RDBMS returned row.
        Args:
            row: dict with table columns as keys.

        Returns:
            *Line* class instance.
        """
        if row.get('dc_id'):
            row.setdefault('dc', {})
            row['dc']['id'] = row.get('dc_id')
            del row['dc_id']

        if row.get('dc_name'):
            row.setdefault('dc', {})
            row['dc']['name'] = row.get('dc_name')
            del row['dc_name']
        return Path(**row)

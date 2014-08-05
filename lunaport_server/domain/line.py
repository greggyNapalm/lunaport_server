# -*- encoding: utf-8 -*-

"""
    lunaport.domain.line
    ~~~~~~~~~~~~~~~~~~~~
    Line related business logic
"""
import string
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from base import BaseFactory, BaseAdaptor, BaseEntrie


class Line(BaseEntrie):
    """
    Line(power line or queue) - district of datacenter.
    """
    attr_required = [
        'id',
        'name',
        'dc',
    ]
    attr_optional = []
        #'dc',
    #]


class LineAdaptor(BaseAdaptor):
    __just_inherit = True


class LineBuilder(BaseFactory):
    """ Line instance static fabric.
    """
    target_struct = Line
    req_attr_allowed = [
        'id',
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
        strip_dc = lambda name: ''.join(
            [el for el in name if el in string.ascii_lowercase])

        msg_rvd = cls.parse_flask_req(r, session)
        msg_rvd.update({
            'dc': {'name': strip_dc(msg_rvd['name'])}
        })
        return Line(**msg_rvd)

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
        return Line(**row)

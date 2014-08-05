# -*- encoding: utf-8 -*-

"""
    lunaport.domain.art
    ~~~~~~~~~~~~~~~~~~~
    DESC
"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from lll_client.tank import TankClinet


class ArtFabric(object):
    """ Arts static builder.
    """
    @classmethod
    def from_test_entrie(cls, test):
        """ Creates class instance from Flask request object.
        Args:
            r: Flask request object.
            session: Flask session object.

        Returns:
            Test class instance.
        """
        tank_c = TankClinet(to=30, fqdn=test.load_src,
                            t_test_id=test.lll['t_tank_id'])

        get_url = lambda art_name: tank_c.compose_art_lnk(art_name)

        def clear_name(f_name):
            """
            Search and remove random(hash) file name part added
            to avoid collisions.
            """
            not_a_hash = ['file', 'run']
            f_name = f_name.encode('ascii', 'ignore')
            f = f_name.split('.')
            if len(f) < 2:
                return f_name

            f = f[0].split('_')
            if (len(f) < 2) or (f[-1] in not_a_hash):
                return f_name

            return f_name.replace('_' + f[-1], '')

        try:
            arts_f_names = tank_c.test_artifacts_lst()['files']
        except Exception as e:
            raise ValueError(str(e))

        return dict(zip(
            map(clear_name, arts_f_names),
            map(get_url, arts_f_names)))

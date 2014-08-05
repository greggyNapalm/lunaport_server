# -*- encoding: utf-8 -*-

"""
    lunaport.domain.job
    ~~~~~~~~~~~~~~~~~~~
    DESC
"""

import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

from lunaport_worker.tasks.check import reduce_test
from .. dao.test import RDBMS as dao_test


class JobFabric(object):
    """ Job static builder.
    """
    req_attr_allowed = [
        'name',
        'args',
        'kwargs',
    ]
    job_names_allowed = [
        'test_reduce'
    ]
    req_attr_allowed_set = set(req_attr_allowed)

    @classmethod
    def test_reduce(cls, **kw):
        assert ('test_id' in kw), 'Required parameter missing: test_id'

        t = dao_test.get_by_id(test_id=int(kw['test_id']))
        if not t:
            raise ValueError('No such test id:{}'.format(kw['test_id']))

        reduce_test.apply_async(
            args=[t.id, t.load_src, t.lunapark['t_tank_id']],
            kwargs={'eval_only': True})
        return None

    @classmethod
    def from_Flask_req(cls, r):
        """ Creates class instance from Flask request object.
        Args:
            r: Flask request object.

        Returns:
            err: Unicode stings with error text if needed.
        """
        if r.mimetype == 'multipart/form-data':
            msg_rv = r.form

        elif r.mimetype == 'application/json':
            msg_rv = r.json
        else:
            raise ValueError('Unsupported mime type')

        if not msg_rv:
            raise ValueError('Can\'t deserialize request body')

        # ImmutableMultiDict to dict cast
        msg_rv = dict((k, v) for k, v in msg_rv.items())
        for k, v in msg_rv.iteritems():
            if isinstance(v, list) and len(v) == 1:
                msg_rv[k] = v[0]

        msg_set = set(msg_rv.keys())

        if not msg_set.issubset(cls.req_attr_allowed_set):
            err_msg = [
                'Body contains unexpected params:',
                str(list(msg_set - cls.req_attr_allowed_set))
            ]
            raise ValueError(' '.join(err_msg))

        if msg_rv.get('name') not in cls.job_names_allowed:
            raise ValueError('Unknown job name:{}'.format(msg_rv.get('name')))

        return getattr(cls, msg_rv.get('name'))(**msg_rv.get('kwargs'))

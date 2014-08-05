# -*- encoding: utf-8 -*-

"""
    lunaport.domain.test
    ~~~~~~~~~~~~~~~~~~~~
    descr
"""

import os
import datetime as dt
import pprint
import json
import StringIO
import copy
import itertools
pp = pprint.PrettyPrinter(indent=4).pprint

import pytz
import dateutil.parser
import msgpack
from lunapark_client.tank import TankClinet

from ..wsgi import app
from .. import load_cfg
from ..dao.host import RDBMS as dao_host
from host import HostBuilder


class BaseLoadTest(object):
    """ Basic load test class"""
    attr_required = [
        'id',
        'status',
        'case',
        'engine',
        'env',
        'name',
        'issue',
        'initiator',
        'load_src',
        'load_dst',
    ]
    attr_optional = [
        'descr',
        'resolution',
        'case_id',
        'generator_cfg',
        'added_at',
        'files',
        'finished_at',
        'lunapark',
        'lunapark_id',
        'started_at',
        'ammo_id',
    ]
    attr_date = ['added_at', 'started_at', 'finished_at']

    def __init__(self, **kw):
        for attr in self.attr_required:
            v = kw.get(attr)
            if not v:
                raise ValueError(
                    '*{}* - required parameter missing.'.format(attr))
            setattr(self, attr, v)

        for attr in self.attr_optional:
            setattr(self, attr, kw.get(attr))

    def as_dict(self, cuted=True, date_iso=False):
        retval = copy.deepcopy(self.__dict__)
        if cuted:  # cut out unnecessary/unsecured fields.
            for k in ['files', ]:
                try:
                    retval.pop(k)
                except Exception:
                    pass

        if date_iso:  # datetime obj JSON serializable in ISO 8601 format.
            for attr in self.attr_date:
                if retval.get(attr):
                    retval[attr] = retval[attr].isoformat()
        return retval

    def as_json(self, cuted=True):
        retval = self.as_dict(date_iso=True)
        return json.dumps(retval)

    def patch(self, diff):
        """ Partially modify class instance.
        Args:
            diff: dict witk att-value pairs.

        Returns:
            Nothing.
        """
        for k, v in diff.iteritems():
            if not hasattr(self, k):
                raise ValueError('Unexpected *Test* diff keys:{}'.format(k))
            setattr(self, k, v)


class YnadexTankTest(BaseLoadTest):
    """ Load test created via Yandex Tank console tool.
    """
    attr_required = [
        'case',
        'engine',
        'env',
        'generator_cfg',
        'name',
        'issue',
        'initiator',
        'load_src',
        'load_dst',
    ]
    attr_optional = [
        'descr',
        'added_at',
        'files',
        'finished_at',
        'lunapark',
        'lunapark_id',
        'started_at',
    ]

    def __init__(self, **kw):
        self.status = kw.get('status', 'pending')
        self.verdict = kw.get('verdict', 'undef')
        self.ammo_path = kw.get('ammo_path', None)

        for attr in self.attr_required:
            v = kw.get(attr)
            if not v:
                raise ValueError(
                    '*{}* - required parameter missing.'.format(attr))
            setattr(self, attr, v)

        for attr in self.attr_optional:
            setattr(self, attr, kw.get(attr))

        if hasattr(self, 'load_src'):
            self.load_src = HostBuilder.from_addr(unknown_addr=self.load_src).fqdn
        if hasattr(self, 'load_dst'):
            self.load_dst = HostBuilder.from_addr(unknown_addr=self.load_dst).fqdn

    def to_monitor_dct(self):
        """
        Create msgpack data with python dict inside for further use.
        Put into Redis, etc.
        """
        struct = {
            'id': self.id,
            'case': {'name': self.case},
            'lunapark_id': self.lunapark_id,
            'status': self.status,
            't_fqdn': self.load_src,
            't_tank_id': self.lunapark['t_tank_id'],
        }
        return msgpack.packb(struct)


class TestAdaptor(object):
    """ Adapt BaseLoadTest instance.
    """
    @staticmethod
    def to_resp(test, jsonify=True):
        """
        HTTP resp suitable representation.
        """
        rv = test.as_dict(date_iso=True)
        if 'case' in rv.keys():
            rv['case'] = {'name': rv['case']}

        if 'case_id' in rv.keys():
            rv['case']['id'] = rv['case_id']
            del rv['case_id']
        if jsonify:
            return json.dumps(rv)
        else:
            return rv


class TestBuilder(object):
    """ Test instance static fabric.
    """
    req_attr_allowed = [
        'autocomplete',
        'case',
        'env',
        'initiator',
        'load_src',
        'lunapark_id',
        'parent_id',
        't_tank_id',
        'tank_fqdn'
    ]
    req_attr_allowed_set = set(req_attr_allowed)
    f_names_allowed = ['phout', 'load_cfg']
    tank_c = TankClinet(to=60)

    @classmethod
    def from_Flask_req(cls, r, session):
        """ Creates class instance from Flask request object.
        Args:
            r: Flask request object.
            session: Flask session object.

        Returns:
            Test class instance.
        """
        if r.mimetype == 'multipart/form-data':
            msg_rv = r.form

        elif r.mimetype == 'application/json':
            msg_rv = r.json
        else:
            raise ValueError('Unsupported mime type')

        # ImmutableMultiDict to dict cast
        msg_rv = dict((k, v) for k, v in msg_rv.items())
        for k, v in msg_rv.iteritems():
            if isinstance(v, list) and len(v) == 1:
                msg_rv[k] = v[0]

        if msg_rv.get('env') == 'luna-tank-api':
            # Test allready launched. New test entrie should be created by
            # fetching  metadata and artefacts from Lunapark APIs.
            msg_rv['initiator'] = msg_rv.get('initiator') or session.get('login')
            return cls.build_from_apis_data(**msg_rv), msg_rv.get('autocomplete', False)
        elif msg_rv.get('env') == 'yandex-tank':
            # Test allready launched manually.
            # New test entrie should be created from
            # request provided configs and artefacts.
            return cls.from_arts(r, session, **msg_rv), msg_rv.get('autocomplete', False)
        elif msg_rv.get('env') is None and r.args.get('force'):
            # New test should be started via Lunapark Tank API.
            # New test entrie should be created based on API responce metadata.
            msg_rv['env'] = 'luna-tank-api-force'
            return cls.launch(r, session, msg_rv), True
        else:
            raise ValueError('Unexpected *env* body param valie')

    @classmethod
    def launch_on_tank(cls, tanks_fqdns, cfg_txt):
        '''
        Walk throuht tanks list and try to launch test on each of them.
        '''
        def call(addr):
            try:
                rv = cls.tank_c.start_test(cfg_txt, fqdn=addr)
                if rv.get('success') is False:
                    raise ValueError(
                        'Tank API call failed:{}'.format(rv.get('error')))
                return rv
            except TankClientError as e:
                raise ValueError('Tank API call failed: {}'.format(e))
            if not rv.get('success'):
                raise ValueError('Tank API call failed: {}'.format(
                    rv.get('error')))

        rv = {}
        for addr in tanks_fqdns:
            try:
                return addr, call(addr)
            except ValueError as e:
                rv[addr] = str(e)
        raise ValueError(str(rv))

    @classmethod
    def msg_to_tanks(cls, msg):
        """
        Extract tanks section from msg, expand short tanks notation to list of
        uniq fqdns.

        Args:
            msg - dict.

        Returns:
            list of str.

        Throws:
            ValueError
        """

        def get_host_by_addr(addr):
            h = dao_host.get_by_fqdn(fqdn=addr)
            if h:
                return h

            try:
                h = dao_host.get_many(ip_addr=addr)
                if h:
                    return h[0][0]
            except Exception:
                pass

            return None

        def proc_tank_el(t):
            if t == 'all':
                return dao_host.get_many(is_tank='True', is_spec_tank='False', per_page=100)[0]

            if isinstance(t, (basestring, unicode)):
                return [HostBuilder.from_addr(unknown_addr=t)]

            if isinstance(t, dict) and t.get('line'):
                line_name = t.get('line')
                return dao_host.get_many(
                    line=line_name, is_tank='True', is_spec_tank='False', per_page=100)[0]

            if isinstance(t, dict) and t.get('dc'):
                dc_name = t.get('dc')
                return dao_host.get_many(
                    dc=dc_name, is_tank='True', is_spec_tank='False', per_page=100)[0]

            raise ValueError('mallformed tank_fqdn cfg entrie:{}'.format(t))

        tanks = msg.get('lunaport', {}).get('tank_fqdn')
        # for backward compatibility lunaport.tank_fqdn may be str and array of str
        if isinstance(tanks, (basestring, unicode)):
            tanks = [tanks]
        if not tanks:
            # not configurated, try to find tanks in the same line than tatgets.
            phantom_secs = (el for el in msg.keys() if el.startswith('phantom'))
            tgt_addrs = [msg[s]['address'] for s in phantom_secs]
            tgt_hosts = map(get_host_by_addr, tgt_addrs)

            if None in tgt_hosts:
                none_idxs = [idx for idx, el in enumerate(tgt_hosts) if el is None]
                raise ValueError(
                    'Can\'t determine line for hosts:{}. Can\'t select tank automatically'.format(
                        [tgt_addrs[idx] for idx in none_idxs]))

            lines = map(lambda h: h.line_name, tgt_hosts)
            if len(lines) == 1:  # all tgts in the same line
                tanks_in_line = dao_host.get_many(line=lines[0], is_tank='True')[0]
                if tanks_in_line:
                    return [host.fqdn for host in tanks_in_line]
                else:
                    raise ValueError('load.cfg malformed, no tanks in line:{}'.format(lines[0]))
            else:
                raise ValueError(
                    'load src and dst lines differs:{}, can\'t select tank automatically'.format(
                        lines))

        tanks_butches = (proc_tank_el(t) for t in tanks)
        decompressed = itertools.chain.from_iterable(b for b in tanks_butches if b)
        suitable_tanks = [h.fqdn for h in decompressed if h]

        if not suitable_tanks:
            raise ValueError('No suitable tanks found')
        return suitable_tanks

    @classmethod
    def launch(cls, r, session, msg_rv):
        """
        Extract load_cfg from request obj, compose tans list from cfg,
        iterate until tank call ends with success.

        Args:
            r - Flask requests obj.
            session - Flask session obj.
            msg_rv - dict, rquest body content.

        Returns:
            YnadexTankTest instance.
        """
        if r.mimetype == 'multipart/form-data':
            cfg_fh = r.files.get('load_cfg')
            if not cfg_fh:
                raise ValueError(
                    'To launch new load test, load_cfg file should be provided.')

            cfg_txt = cfg_fh.stream.getvalue()
            cfg = cls.parse_generator_cfg(cfg_txt, plain_cfg=True)

        elif r.mimetype == 'application/json':
            cfg = r.json
            cls.validate_generator_cfg(cfg)
            cfg_txt = load_cfg.cmpl_cfg(**cfg).getvalue()
        else:
            raise ValueError('Media type not supported')

        tanks = cls.msg_to_tanks(msg_rv)
        tank_fqdn, tank_msg = cls.launch_on_tank(tanks, cfg_txt)

        msg_to_build = {k: v for k, v in msg_rv.iteritems() if k in cls.req_attr_allowed}
        msg_to_build.update({
            't_tank_id': tank_msg.get('id'),
            'tank_fqdn': tank_fqdn,
            'name': cfg.get('meta', {}).get('job_name'),
            'descr': cfg.get('meta', {}).get('job_dsc'),
            'issue': cfg.get('meta', {}).get('task'),
            'load_dst': cfg.get('phantom', {}).get('address'),
            'case': msg_rv.get('case') or cfg.get('lunaport', {}).get('case'),
            'initiator': cfg.get('lunaport', {}).get('initiator') or msg_rv.get('initiator') or session.get('login')
        })
        if msg_to_build.get('issue'):
            msg_to_build['issue'] = msg_to_build['issue'].lower()

        if msg_to_build.get('load_dst'):
            msg_to_build['load_dst'] = cls.extract_dst_addr(msg_to_build['load_dst'])
 
        return cls.build_from_apis_data(**msg_to_build)

    @staticmethod
    def extract_dst_addr(ph_addr):
        if '[' in ph_addr:
            pair = ph_addr.rsplit(':', 1)
            if len(pair) != 2:
                raise ValueError('Phantom cfg *address* field malformed')
            derty_addr, port = pair
            addr = derty_addr.lstrip('[').rstrip(']')
            return addr
        return ph_addr


    @classmethod
    def build_from_apis_data(cls, **kw):
        for p in ['t_tank_id']:
            assert p in kw, '*{}* - required parameter missing.'.format(p)
        params = {'files': {}}
        t_summary = {}
        if kw.get('luna_id'):
            try:
                    l_test_id=kw.get('luna_id')).json().pop()
        t_summary.update(kw)

        if t_summary.get('jira_task'):
            t_summary['issue'] = t_summary['jira_task'].lower()
        try:
            cfg_str = cls.tank_c.get_generator_cfg(fqdn=t_summary['tank_fqdn'],
                                                   t_test_id=t_summary.get('t_tank_id'))
        except TankClientError as e:
            raise ValueError('Tank API call failed: {}'.format(e))

        assert cfg_str, 'Can\'t fetch load.cfg from tank.'
        params['generator_cfg'] = cls.parse_generator_cfg(cfg_str,
                                                          plain_cfg=True)
        params = cls.merge_generator_cfg(params)

        params.update({
            'case': t_summary.get('case'),
            'env': t_summary.get('env', 'luna-tank-api'),
            'name': t_summary['name'],
            'descr': t_summary.get('dsc') or t_summary.get('descr'),
            'issue': t_summary.get('issue'),
            'initiator': t_summary['initiator'],
            'load_src': t_summary.get('tank') or t_summary.get('tank_fqdn'),
            'load_dst': t_summary.get('srv') or t_summary.get('load_dst'),
            'lunapark_id': t_summary.get('luna_id'),
        })
        if 'fd' in t_summary:
            params['started_at'] = msk_iso_to_utc(t_summary['fd'])
        if 'lunapark' in params:
            # XXX: Removing useless and buggy content
            params['lunapark']['command_line'] = None

        return YnadexTankTest(**params)

    @classmethod
    def from_arts(cls, r, session, **kw):
        """ Creates YnadexTankTest instance from HTTP request body form params
        and attached files.
        """
        params = {'files': {}}
        now = dt.datetime.now
        f_names_allowed = ['phout', 'load_cfg']
        attr_allowed = [
            'case',
            'env',
            'initiator',
            'parent_id',
            'load_src',
            'autocomplete',
        ]

        attr_allowed_set = set(attr_allowed)
        msg_set = set(kw.keys())

        if not msg_set.issubset(attr_allowed_set):
            err_msg = [
                'Body contains unexpected params:',
                str(list(msg_set - attr_allowed_set))
            ]
            raise ValueError(' '.join(err_msg))

        if not r.files:
            raise ValueError('Request shude contains files:load_cfg and phout')

        if sorted(f_names_allowed) != sorted(r.files.keys()):
            raise ValueError('Wrong files names in body.')

        for k, v in r.files.iteritems():
            f_name = '{}-{}'.format(k, now().strftime('%s.%f'))
            params['files'][k] = os.path.join(
                app.config['ARTS_UPLOAD_PATH'], f_name)
            v.save(params['files'][k])

        params['generator_cfg'] = cls.parse_generator_cfg(
            params['files']['load_cfg'])
        params = cls.merge_generator_cfg(params)

        for k in attr_allowed:
            params[k] = kw.get(k)

        # use auth login if usr creates new test authed by login and
        # didn't specified *initiator* param in request.
        params['initiator'] = kw.get('initiator') or session.get('login')

        return YnadexTankTest(**params)

    @classmethod
    def parse_generator_cfg(cls, cfg, plain_cfg=False, validate=True):
        """ Read load.cfg(INI format) file from local file system, parse it,
            validate content structure.

            cfg - str, Path to file with config or config content as string.
            plain_cfg - bool, True if whole config as param given and False if
                       file path given.
        """
        p = load_cfg.Parser()
        if plain_cfg:
            cfg = StringIO.StringIO(cfg)

        try:
            if plain_cfg:
                p.readfp(cfg)
            else:
                p.read(cfg)
        except Exception:
            raise ValueError('Can\'t read generator config(load.cfg) as .ini')
        cfg = p.as_dict()

        clr_el = lambda n: n.lstrip().lstrip('u').lstrip("'").lstrip().rstrip().rstrip('\'')

        def proc_tank_fqdn_el(el):
            el = el.lstrip().rstrip()
            if el.startswith('{'):
                k, v = map(clr_el, el.lstrip('{').rstrip('}').split(':'))
                return {k: v}
            else:
                return clr_el(el)

        # XXX: CFG types cast, default INI -> JSON cast.
        if cfg.get('lunaport', {}).get('tank_fqdn'):
            tank_fqdn_sct = cfg.get('lunaport').get('tank_fqdn')
            if tank_fqdn_sct.startswith('['):
                # tank_fqdn type array
                elements_as_str = tank_fqdn_sct.lstrip('[').rstrip(']').split(',')
                elements = [proc_tank_fqdn_el(el) for el in elements_as_str]
                cfg['lunaport']['tank_fqdn'] = [e for e in elements if e]
            else:
                # tank_fqdn type string - sing tank fqdn
                cfg['lunaport']['tank_fqdn'] = [tank_fqdn_sct]

        if validate:
            load_cfg.validate(cfg)
        return cfg

    @classmethod
    def validate_generator_cfg(cls, cfg):
        """ cfg - dict
        """
        load_cfg.validate(cfg)

    @classmethod
    def merge_generator_cfg(cls, params):
        """ Merge generator_cfg content to existing params.
        """
        try:
            params.update({
                'name': params['generator_cfg']['meta']['job_name'],
                'descr': params['generator_cfg']['meta'].get('job_dsc'),
                'issue': params['generator_cfg']['meta']['task'],
            })
        except Exception as e:
            raise ValueError(
                'Malformed generator_cfg structure, because: {}'.format(e))

        if params['generator_cfg'].get('phantom'):
            params.update({
                'engine': 'phantom',
                'load_dst': params['generator_cfg']['phantom']['address'],
                'ammo_path': params['generator_cfg']['phantom'].get('ammofile'),
            })

        if 'issue' in params:
            params['issue'] = params['issue'].lower()
        return params

    @classmethod
    def from_row(cls, **row):
        """ Creates class instance from RDBMS returned row.
        Args:
            row: dict with table columns as keys.

        Returns:
            YnadexTankTest class instance.
        """
        return BaseLoadTest(**row)


def fetch_luanapark_repr(lunapark_test_id):
    """
    Fetch *possibly* existing load test details from Lunapark.
    """
    test_repr = {}
    try:
                                       codes_allowed=[200, 404])
    if t_summary.status_code == 404:
        return None

    try:
        test_repr.update({
        })
    except Exception as e:
        if 'stpd_file =' in cfg_info.text:
            engine = 'phantom'
        elif 'jmeter_path' in cfg_info.text:
            engine = 'jmeter'
        else:
            engine = 'unknown'

        test_repr.update({
            'engine': engine,
        })

    if len(cfg_info.text) == 0:
        # originally resource was placed in memecache and
        # may be missing(empty responce body).
        test_repr['tank_test_id'] = None
    else:
        test_repr['tank_test_id'] = parse_tank_test_id(cfg_info.text)
    return test_repr


def fetch_tests_offline():
    """
    Fetch butch of test in offline state sort by id descending.
    """
    try:
    if tests_offline.status_code == 404:
        return None

    return sorted([el.get('job_number') for el in tests_offline.json()])


def parse_tank_test_id(configinfo):
    # and .INI parsing part will be replaced.
    cfg = TestBuilder.parse_generator_cfg(configinfo, plain_cfg=True,
                                          validate=False)
    return cfg.get('tank', {}).get('api_jobno')


def msk_iso_to_utc(date_iso_str):
    """ Convert 'Europe/Moscow' local time stamp to UTC stamp.
    """
    local = pytz.timezone('Europe/Moscow')
    local_dt = local.localize(dateutil.parser.parse(date_iso_str), is_dst=None)
    return local_dt.astimezone(pytz.utc)

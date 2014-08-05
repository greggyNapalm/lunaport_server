#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
    load_cfg
    ~~~~~~~~

    Contains dict with schemat to use with validictory module.
"""

import copy
import StringIO
import ConfigParser
import pprint
pp = pprint.PrettyPrinter(indent=4).pprint

import validictory

SCHEMA = {
    'type': 'object',
    'properties': {
        'meta': {
            'type': 'object',
            'properties': {
                'task': {'type': 'string'},
                'job_name': {'type': 'string'},
                'job_dsc': {'type': 'string', 'required': False},
                'ver': {'type': 'string', 'required': False},
                'operator': {'type': 'string', 'required': False},
                'notify': {'type': 'string', 'required': False},
                'regress': {'type': 'string', 'required': False},
                'component': {'type': 'string', 'required': False},
            }
        },
        'tank': {
            'type': 'object',
            'required': False,
            'properties': {
                'artifacts_base_dir': {'type': 'string', 'required': False},
            }
        },
        'phantom': {
            'type': 'object',
            'properties': {
                'instances_schedule': {'type': 'string', 'required': False, 'blank': True},
                'rps_schedule': {'type': 'string', 'required': False, 'blank':True},
                'ammofile': {'type': 'string', 'required': False, 'blank': True},
                'address': {'type': 'string'},
                'port': {'type': 'string', 'required': False},
                'ssl': {'type': 'string', 'required': False},
                'header_http': {'type': 'string', 'required': False},
                'headers': {'type': 'string', 'required': False},
                'writelog': {'type': 'string', 'required': False},
                'header_http': {'type': 'string', 'required': False},
                'uris': {'type': 'string', 'required': False, 'blank': True},
                'connection_test': {'type': 'string', 'required': False},
            }
        },
        #'autostop': {
        #    'type': 'object',
        #    'required': False,
        #    'properties': {
        #        'autostop': {'type': 'string', 'required': False},
        #    }
        #},
        'monitoring': {
            'type': 'object',
            'required': False,
            'properties': {
                'config': {'type': 'string', 'required': False},
            }
        },
        'aggregator': {
            'type': 'object',
            'required': False,
            'properties': {
                'time_periods': {'type': 'string', 'required': False},
                'monitoring_config': {'type': 'string', 'required': False},
            }
        },
        'shellexec': {
            'type': 'object',
            'required': False,
            'properties': {
                'end': {'type': 'string', 'required': False},
                'postprocess': {'type': 'string', 'required': False},
            }
        },
    },
}


class Parser(ConfigParser.ConfigParser):
    """ Add dict representation to default ConfigParser.
    """
    def as_dict(self):
        d = dict(self._sections)
        for k in d:
            d[k] = dict(self._defaults, **d[k])
            d[k].pop('__name__', None)
        return d


def validate(cfg, schema=SCHEMA):
    """ Check cfg dict structure: required keys and their types.
    Args:
        cfg: dict, data to validate.
        schema: dict, validation rules.

    Returns:
        Raise exception on invalid sample.
    """
    validictory.validate(cfg, schema)
    return True


def el_to_msec(el):
    if el.endswith('s'):
        return int(el.rstrip('s')) * 1000
    elif el.endswith('m'):
        return int(el.rstrip('m')) * 1000 * 60
    return int(el)


def time_periods_to_msec(periods):
    """ Convert load.cfg time_periods parameter value dimension to seconds.
    Args:
        periods: str, Yandex tank load.cfg param.

    Returns:
        list of int, in seconds.
    """
    return sorted(map(el_to_msec, periods.split(' ')))


def cmpl_cfg(*args, **kw):
    """
    Create buffer obj with INI formated yandex tank config inside.
    Args:
        args: not used.
        kwargs: dict with cfg sections.

    Returns:
        StringIO obj instance with INI cfg inside.
    """
    sections = {
        'meta': ['task', 'job_name', 'job_dsc', 'ver', 'operator', 'notify', 'regress', 'component'],
        'tank': ['artifacts_base_dir'],
        'phantom': [
            'ssl',
            'header_http',
            'headers',
            'rps_schedule',
            'instances_schedule',
            'ammofile',
            'writelog',
            'address',
            'port',
            'header_http',
            'instances',
            'uris',
            'connection_test',
        ],
        'autostop': ['autostop'],
        'monitoring': ['config'],
        'aggregator': ['time_periods', 'monitoring_config'],
        'shellexec': ['end', 'postprocess'],
        'lunaport': ['case', 'tank_fqdn', 'parent_id', 'tags_delimtr'],
    }

    skeleton = copy.deepcopy(sections)
    for el in filter(lambda k: k.startswith('phantom'), kw.keys()):
        skeleton.update({el: sections['phantom']})

    config = Parser()

    def cast_sec_val(v):
        if isinstance(v, list):
            v = str(v)
        return v.encode('UTF-8')
    for section, params in skeleton.iteritems():
        config.add_section(section)
        for param in params:
            try:
                config.set(section, param, cast_sec_val(kw[section][param]))
                #print type(kw[section][param]), cast_sec_val(kw[section][param])
            except KeyError:
                pass

    buf = StringIO.StringIO()
    config.write(buf)
    return buf

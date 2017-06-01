import os
import re
import logging

import ConfigParser

from . import api


log = logging.getLogger(__name__)


DEFAULT_CONFIG = {
    'endpoint': 'http://localhost:8081/api/v1/servers/localhost',
}


def load_config(custom_path=''):
    config = ConfigParser.ConfigParser()
    paths = ['./pypdns.ini',
             '~/.config/pypdns.ini']
    if custom_path:
        paths.insert(0, os.path.realpath(custom_path))
    config.read(paths)
    return config


def parse_config(cfg, ext_config={}):
    config = {}
    try:
        options = cfg.options('pypdns')
    except ConfigParser.NoSectionError:
        log.debug('No config files provided and default not present')
        options = []

    for option in options:
        config[option] = cfg.get('pypdns', option)

    for ckey, cvalue in DEFAULT_CONFIG.iteritems():
        if ckey not in config:
            config[ckey] = cvalue

    for k in ('endpoint', 'apikey'):
        if k in ext_config and ext_config[k] is not None:
            config[k] = ext_config[k]

    assert (config.get('endpoint') is not None and
            config.get('apikey') is not None), 'Configuration not found'

    return config


class PyPDNS(object):

    def __init__(self, ext_config={}):
        cfg = load_config(ext_config.get('config_path'))

        self.config = parse_config(cfg, ext_config)
        self.zones_api = api.ZonesAPI(self.config)

    def zones_list(self, name='.*'):
        """
        Get all zone from remote pdns API

        :return: List of zone
        :rtype:
        """
        ret, code = self.zones_api.get_zones()
        if code != 200:
            return ret

        result = []
        name = re.compile(name)
        for zone in ret:
            match = name.match(zone['name'])
            if match:
                result.append(zone)
        return result

    def zones_get(self, zone_id, name='.*', _type='.*'):
        """
        Return zone data.

        :param zone_id: Zone name
        :type zone_id: String
        :param name: Filter rrsets of given zone on name
        :type name: String
        :param _type: Filter rrsets of given zone on type
        :type _type: String
        :return: zone data as dict or False if not found.
        :rtype: dict
        """
        ret, code = self.zones_api.get_zone(zone_id)
        patterns = {}
        result = []
        if code != 200:
            return ret
        patterns['name'] = re.compile(name)

        patterns['type'] = re.compile(_type)

        for record_set in ret['rrsets']:
            match = True
            for key, pattern in patterns.iteritems():
                match &= bool(pattern.match(record_set[key]))
            if match:
                result.append(record_set)

        return result

    def zones_create(self, name, kind='NATIVE', soa=None, nameservers=[],
                     soa_edit='DEFAULT'):
        """
        Creates a Zone

        :param name: Zone name
        :type name: String
        :param soa: Start of authority, override default config from pdns server
        :type name: String
        :param nameservers: List of nameservers for the given zone
        :type nameservers: list
        :param soa_edit: SOA edit behaviour for serial update
        :type soa_edit: String
        """
        soa = soa or self.config.get('default-soa')
        nameservers = nameservers or self.config.get('nameservers')
        if not (soa and nameservers):
            raise ValueError('Missing soa or nameservers value')

        data = {
            'name': name,
            'kind': kind,
            'nameservers': nameservers,
            'soa_edit': soa_edit,
        }
        ret, code = self.zones_api.create_zone(data)
        return ret

    def record_add(self, zone_name, record_name, content, type_='A',
                   changetype='REPLACE', ttl=3600, no_ptr=False, disabled=False):
        """
        Add or replace a record

        :param zone_name: Zone to add record to
        :type zone_name: String
        :param record_name: Name of the record
        :type record_name: String
        :param content: Content of the record
        :type content: String
        :param type_: record's type
        :type type_: String
        :param changetype: Update behaviour, REPLACE or DELETE, default to REPLACE
        :type changetype: String
        :param ttl: record's type, default to A
        :type ttl: int
        :param no_ptr: For A or AAAA record, default is to automatically add reverse, set this to True if not wanted
        :type no_ptr: bool
        :param disabled: Disable record, default to False
        :type disabled: bool
        """
        record_name = (record_name if record_name.endswith('.')
                        else record_name + '.')
        name = record_name + zone_name
        if not name.endswith('.'):
            name += '.'

        data = {
            'rrsets': [
                {'name': name,
                 'type': type_,
                 'ttl': ttl,
                 'changetype': changetype,
                 'records': [
                     {'content': content,
                      'set-ptr': not no_ptr,
                      'disabled': disabled
                    }
                 ]}
            ]
        }
        ret, code = self.zones_api.update_records(zone_name, data)
        return ret

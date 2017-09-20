import os
import re
import logging
import datetime

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
        if ext_config.get(k) is not None:
            config[k] = ext_config[k]

    assert (config.get('endpoint') is not None and
            config.get('apikey') is not None), 'Configuration not found'

    return config


class PyPDNS(object):

    _interactive = False

    def __init__(self, ext_config={}):
        cfg = load_config(ext_config.get('config_path'))

        self.config = parse_config(cfg, ext_config)
        self.zones_api = api.ZonesAPI(self.config)
        self.search_api = api.SearchAPI(self.config)

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

            for comment in record_set.get('comments', []):
                if comment['modified_at']:
                    comment['modified_at'] = datetime.datetime.fromtimestamp(
                        comment['modified_at']).isoformat()
            if match:
                result.append(record_set)

        return result

    def zones_create(self, name, kind='NATIVE', soa=None, nameservers=[],
                     soa_edit='INCEPTION-INCREMENT', soa_ttl=7200):
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
            'soa_edit_api': soa_edit,
            'rrsets': [
                {'name': name,
                 'type': 'SOA',
                 'ttl': soa_ttl,
                 'records': [{'content': soa, 'disabled': False}]}
            ]
        }
        ret, code = self.zones_api.create_zone(data)
        return ret, code

    def record_add(self, zone_name, record_name, contents, comment, type_='A',
                   changetype='REPLACE', ttl=3600, reverse=False, disabled=False,
                   override=False):
        """
        Add or replace a record, Return 2-tuple : response body, response code
        if record exists and override is set to False : return error message
        and -1 error code.

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
        :param reverse: For A or AAAA record, default is to False, set this to True for creating a reverse record
        :type reverse: bool
        :param disabled: Disable record, default to False
        :type disabled: bool
        """
        record_name = (record_name if record_name.endswith('.')
                       else record_name + '.')

        type_ = type_.upper()

        name = (record_name + zone_name if (type_ not in ('SOA',) and
                                            record_name != '.')
                else zone_name)

        if not override:
            # record already exists ?
            existing_record = self._get_record(name, type_)
            if existing_record:
                if not self._interactive:
                    return ('Specify override=True for erasing existing record',
                            -1)
                else:
                    valid = self._validate_override(existing_record)
                    if not valid:
                        return False

        if not name.endswith('.'):
            name += '.'

        records = []

        for content in contents.split(','):
            record = {
                'content':  content,
                'set-ptr':  reverse,
                'disabled': disabled
            }
            records.append(record)

        data = {
            'rrsets': [
                {'name': name,
                 'type': type_,
                 'ttl': ttl,
                 'changetype': changetype,
                 'records': records,
                 'comments': [{'account': os.environ['USER'],
                               'content': comment,
                               }
                              ]
                 }
            ]
        }
        ret, code = self.zones_api.update_records(zone_name, data)
        return ret, code

    def search(self, term, object_type=None, zone=None, rtype=None,
               max_results=None):
        """
        Search for data in zone & record

        :param term: term to search, use * for wildcard char and ? for a single wildcard char
        :type term: String
        :param object_type: filter results, zone or record
        :type object_type: String
        :param zone: filter results record on a specific zone (sets object_type = record)
        :type zone: String
        :param rtype: filter on the given record's type (implies object_type = record)
        :param max_results: Limit number of results, default to None
        :rtype max_results: int
        """
        results, sts_code = self.search_api.search(term, max_results)
        object_type = 'record' if zone or rtype else object_type
        if not object_type or sts_code != 200:
            return results

        filtered = [rec for rec in results if rec['object_type'] == object_type]

        if zone:
            zone = zone + '.' if not zone.endswith('.') else zone
            filtered = [rec for rec in filtered if rec.get('zone') == zone]

        if rtype:
            filtered = [rec for rec in filtered if rec.get('type') == rtype]

        return filtered

    def add(self, record_name, content, comment, rtype,ttl=3600, reverse=False,
            override=False):
        record, zone = self._construct_names(record_name)
        if not zone:
            log.info('Cannot find zone for record : %s', record_name)
            return False

        return self.record_add(zone, record, content, comment, type_=rtype,
                               ttl=ttl, reverse=reverse, override=override)

    def delete(self, record_name, comment, rtype, override=False):
        record, zone = self._construct_names(record_name)
        if not zone:
            log.info('Cannot find zone for record : %s', record_name)
            return False

        return self.record_add(zone, record, '', comment, type_=rtype,
                               override=override, changetype='DELETE')

    def _get_record(self, name, rtype):
        search = self.search(name)
        return next((rr for rr in search if rr.get('name') == name + '.' and
                                            rr.get('type') == rtype),
                    None)

    def _validate_override(self, record):
        valid = False
        while not valid:
            replace = raw_input('Warning, the record already exists with the '
                                'following data %s, replace it ? Y/n :'
                                '' % record)
            if replace.lower() not in ('y','n','yes','no'):
                continue
            if replace.lower() in ('n', 'no'):
                log.info('Exiting with no changes on existing record')
                valid = False
                break
            else:
                valid = True
        return valid

    def _zone_exists(self, zone):
        resp = self.zones_get(zone)
        if 'error' in resp:
            res = None
        else:
            res = resp
        return res

    def _construct_names(self, name):
        sub_names = name.split('.')
        # Iterates on sub domains to find record name & zone, use api to find
        # the first name matching a zone.
        zone = []
        record = []
        for i in xrange(0, len(sub_names)):
            sub_zone = '.'.join(sub_names[i:])
            search = self._zone_exists(sub_zone)
            if search:
                zone = sub_names[i:]
                record = [rr for rr in sub_names if rr not in sub_names[i:]]
                break
        return ('.'.join(record), '.'.join(zone))

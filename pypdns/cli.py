"""
pypdns

Usage:
    pypdns zones list [-c <cfg_pth>] [--log <log_level>] [--name <name>]
    pypdns zones get <zone_name> [--log <log_level>] [-c <cfg_pth>] [--name <name>] [--type <type>]
    pypdns zones create <zone_name> [-c <cfg_pth>] [--log <log_level>] [--soa <soa>] [--kind <kind>] [--nameservers=<nameservers>] [--soa-edit <soa_edit>] [--soa-ttl <soa_ttl>]
    pypdns record add <zone_name> <record_name> <content> <comment> --rtype <type> [--changetype <changetype>] [--ttl <ttl>] [--no-ptr] [--disabled] [-c <cfg_pth>] [--log <log_level>]
    pypdns search <term> [--otype <object_type>] [--zone <zone>] [--rtype <type>] [--max-results <max_results>] [-c <cfg_pth>] [--log <log_level>]
    pypdns (-h | --help)
    pypdns --version

Options:
    -c <cfg_pth> --config=<cfg_pth>     Path of configuration file, if not provided default to: ./pypdns.ini, ~/.config/pypdns.ini
    -h --help       Show this screen
    --version       Show version
    --endpoint <api_endpoint>        Override config file for pdns api endpoint
    --apikey <api_key>               Override config file for pdns api api key
    --log <log_level>                Set log level [default: ERROR]
    --name <name>                    Filter results on name for a given zone, regex format [default: .*]
    --type <type>                    Filter results on type for a given zone, regex format [default: .*]
    --soa <soa>                      SOA valid string, override default_soa in config file
    --soa-ttl <soa_ttl>              SOA ttl, [default: 7200]
    --kind <kind>                    Zone type, [default: NATIVE]
    --nameservers=<nameservers>      List of namservers for zone, override value from config file
    --soa_edit <soa_edit>            Soa edit behaviour for the zone, [default: DEFAULT]
    --rtype <type>                   Record's type
    --no-ptr                         Do not add reverse when adding A or AAAA record
    --changetype <changetype>        Record update behaviour [default: REPLACE]
    --disabled                       Disable record
    --ttl <ttl>                      Record's ttl [default: 3600]
    --otype <object_type>            Filter search result, one of : record or zone [default: record]
    --zone <zone>                    Filter search result on zone name (sets object_type to record)
    --max-results <max_results>      Limit search results
"""
import logging

from docopt import docopt
from pprint import pprint

from . import __version__ as VERSION
from .pypdns import PyPDNS


def main():
    options = docopt(__doc__, version=VERSION)
    cfg = {
        'config_path': options.get('--config'),
        'endpoint': options.get('--endpoint'),
        'apikey': options.get('--apikey')
    }
    logging.basicConfig()
    log_level = getattr(logging, options['--log'].upper(), None)
    if not isinstance(log_level, int):
        raise ValueError('Invalid log level: %s' % log_level)

    logger = logging.getLogger()
    logger.setLevel(log_level)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info('Start')
    pdns_api = PyPDNS(cfg)

    if 'zones' in options and options['zones']:
        if 'list' in options and options['list']:
            pprint(pdns_api.zones_list(options['--name']))

        if 'get' in options and options['get']:
            pprint(pdns_api.zones_get(options['<zone_name>'],
                                      options['--name'], options['--type']))

        if 'create' in options and options['create']:
            nameservers = options.get('--nameservers', [])
            nameservers = nameservers and nameservers.split(',')

            pprint(pdns_api.zones_create(options['<zone_name>'],
                                         kind=options['--kind'],
                                         soa=options['--soa'],
                                         nameservers=nameservers,
                                         soa_edit=options['--soa-edit'],
                                         soa_ttl=options['--soa-ttl']))

    if options['record']:
        if options['add']:
            pprint(pdns_api.record_add(options['<zone_name>'],
                                       options['<record_name>'],
                                       options['<content>'],
                                       options['<comment>'],
                                       type_=options['--rtype'],
                                       changetype=options['--changetype'],
                                       ttl=int(options['--ttl']),
                                       no_ptr=options['--no-ptr'],
                                       disabled=options['--disabled']))
    if options['search']:
        pprint(pdns_api.search(options['<term>'],
                               object_type=options['--otype'],
                               zone=options['--zone'],
                               rtype=options['--rtype'],
                               max_results=options['--max-results']))

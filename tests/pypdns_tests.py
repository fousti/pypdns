import os

import pytest

from pypdns import PyPDNS


@pytest.fixture
def conf_from_file():
    path =  os.path.join(os.path.dirname(__file__), '..', 'pypdns-test.ini')
    return {'config_path': path}


@pytest.fixture
def conf_from_dict():
    return {
        'endpoint': 'http://pdns.test:8081',
        'apikey': 'testapikey'
    }


def test_config_from_file(conf_from_file):
    pdns_api = PyPDNS(conf_from_file)
    cfg = pdns_api.config
    assert cfg['endpoint'], 'http://localhost:8080'
    assert cfg['apikey'], 'myapikey'


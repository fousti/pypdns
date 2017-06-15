import requests
import logging


log = logging.getLogger(__name__)


class PdnsAPI(object):

    collection_url = ''
    url = ''
    _session = None

    def __init__(self, config):
        self.endpoint = config['endpoint']
        self.apikey = config['apikey']

    @property
    def session(self):
        if not self._session:
            self._session = requests.Session()
            self._session.headers.update({'X-Api-Key': self.apikey})
        return self._session

    def _process_resp(self, resp, sts_code):
        data = None
        try:
            data = resp.json()
        except ValueError:
            log.debug("No json response found.")
            data = resp.text

        return data, sts_code

    def build_url(self, _id, url):
        if not url and _id:
            url = self.endpoint + self.url.format(_id)
        elif not _id and not url:
            raise ValueError('Provide either an resource id or a full url to '
                             'call')
        return url

    def _call(self, verb, url, data={}, params={}, headers={}):
        if headers:
            self.session.headers.update(headers)

        log.info('Call %s with data %s', url, data)
        resp = self.session.request(verb, url, json=data, params=params)
        status_code = resp.status_code
        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            log.debug('Error occured, endpoint : %s, apikey : %s',
                      url, self.apikey)
            return resp, status_code

        except requests.Timeout:
            log.error('Request Timeout to %si', url)
            return False, status_code
        except requests.RequestException:
            log.error('Requests Error')
            return False, status_code
        else:
            return resp, status_code

    def collection_get(self, params={}):
        url = self.endpoint + self.collection_url
        return self._call('GET', url, params=params)

    def get(self, url=None, _id=None, params={}):
        url = self.build_url(_id, url)
        return self._call('GET', url, params=params)

    def collection_post(self, data):
        url = self.endpoint + self.collection_url
        return self._call('POST', url, data=data)

    def patch(self, data, _id=None, url=None):
        url = self.build_url(_id, url)
        return self._call('PATCH', url, data=data)


class ZonesAPI(PdnsAPI):
    collection_url = '/zones'
    url = '/zones/{}'

    def get_zones(self):
        return self._process_resp(*self.collection_get())

    def get_zone(self, zone_id):
        return self._process_resp(*self.get(_id=zone_id))

    def create_zone(self, data):
        return self._process_resp(*self.collection_post(data))

    def update_records(self, zone_name, data):
        return self._process_resp(*self.patch(data, _id=zone_name))


class SearchAPI(PdnsAPI):
    collection_url = '/search-data'
    url = ''

    def search(self, term, max_results=None):
        params = {'q': term}
        if max_results:
            params['max'] = max_results
        return self._process_resp(*self.collection_get(params=params))

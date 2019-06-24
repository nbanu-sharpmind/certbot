"""Module provider for DNS Simple"""
from __future__ import absolute_import
import json
import logging

import requests
import pprint

from lexicon.providers.base import Provider as BaseProvider

LOGGER = logging.getLogger(__name__)

NAMESERVER_DOMAINS = ['checkdomain.de']

def provider_parser(subparser):
    """Configure provider parser for Checkdomain"""
    subparser.add_argument(
        "--auth-token", help="specify api token for authentication")

    # subparser.add_argument(
    #    "--auth-username", help="specify email address for authentication")
    # subparser.add_argument(
    #    "--auth-password", help="specify password for authentication")
    # subparser.add_argument(
    #    "--auth-2fa",
    #    help="specify two-factor auth token (OTP) to use with email/password authentication")


class Provider(BaseProvider):
    """Provider class for Checkdomain"""

    def __init__(self, config):
        super(Provider, self).__init__(config)
        self.domain_id = None
        self.api_endpoint = self._get_provider_option(
            'api_endpoint') or 'https://api.checkdomain.de/v1'

        LOGGER.debug('check-domain module initialized....')

    def _authenticate(self):
        LOGGER.debug('IN: _authenticate')

        json_result = self._get('/domains?limit=100')

        # find our domain
        all_domains = json_result['_embedded']['domains']

        domains_found = [x for x in all_domains if x['name'] == self.domain]

        # pprint.pprint(domains_found)

        if (len(domains_found) > 0):
            self.domain_id = domains_found[0]['id']
            print("Found domain id %d for domain name %s" % (self.domain_id, self.domain))
        else:
            print("Nothing found")
            raise Exception('Domain not found')

    # Create record. If record already exists with the same content, do nothing
    def _create_record(self, rtype, name, content):
        LOGGER.debug('IN: _create_record')

        # check if record already exists
        existing_records = self._list_records(rtype, name, content)
        LOGGER.debug('in _create_record---> existing record:%d' % len(existing_records))

        if len(existing_records) == 1:
            return True

        # record = {
        #     'type': rtype,
        #     'name': self._relative_name(name),
        #     'content': content
        # }

        record = {
            'type': rtype,
            'name': self._relative_name(name),
            'value': content
        }

        # if self._get_lexicon_option('ttl'):
        #     record['ttl'] = self._get_lexicon_option('ttl')
        # if self._get_lexicon_option('priority'):
        #     record['priority'] = self._get_lexicon_option('priority')
        # if self._get_provider_option('regions'):
        #     record['regions'] = self._get_provider_option('regions')

        record['ttl'] = 90
        record['priority'] = 0

        # payload = self._post(
        #     '/{0}/zones/{1}/records'.format(self.account_id, self.domain), record)

        payload = self._post(
            '/domains/{0}/nameservers/records'.format(self.domain_id), record)

        LOGGER.debug('create_record: %s', 'id' in payload)
        return 'id' in payload

    # List all records. Return an empty list if no records found
    # type, name and content are used to filter records.
    # If possible filter during the query, otherwise filter after response is received.
    def _list_records(self, rtype=None, name=None, content=None):
        LOGGER.debug('IN: _list_records ---> rtype=%s, name=%s, content=%s' % (rtype,name, content) )

        #url = '/domains/{0}/nameservers/records?limit=100'.format(self.domain_id)
        url = '/domains/{0}/nameservers/records?limit=100'.format(self.domain_id)

        records = []
        payload = {}

        next_url = url
        while next_url is not None:

            payload = self._get(next_url)

            if '_links' in payload \
                    and 'pages' in payload['_links'] \
                    and 'next' in payload['_links']['pages']:
                next_url = payload['_links']['pages']['next']

            else:
                next_url = None

            LOGGER.debug('888888888, next_url=%s' % (next_url) )

            #for record in payload['domain_records']:
            for record in payload['_embedded']['records']:

                if '_links' in record:

                    href = record['_links']['self']['href']

                    link_id = href.split("/")[-1]

                    processed_record = {
                        'type': record['type'],
                        'name': "{0}.{1}".format(record['name'], self.domain_id),
                        'ttl': '',
                        'content': record['value'],
                        'id': link_id
                    }
                    records.append(processed_record)

        if rtype:
            records = [record for record in records if record['type'] == rtype]
        if name:
            records = [record for record in records if record['name']
                       == self._full_name(name)]
        if content:
            records = [
                record for record in records if record['value'].lower() == content.lower()]

        LOGGER.debug('in _list_records--->number of records with href and desired name and type: %s' % (records))
        return records

    # Create or update a record.
    def _update_record(self, identifier, rtype=None, name=None, content=None):

        LOGGER.debug('in UPDATE.., identifier=%s, rtype=%s, name=%s, content=%s' % (identifier, rtype,name, content) )

        data = {}

        if identifier is None:
            records = self._list_records(rtype, name, content)
            identifiers = [record["id"] for record in records]
        else:
            identifiers = [identifier]

        if name:
            data['name'] = self._relative_name(name)
        if content:
            data['content'] = content
        if self._get_lexicon_option('ttl'):
            data['ttl'] = self._get_lexicon_option('ttl')

        # if self._get_lexicon_option('priority'):
        #     data['priority'] = self._get_lexicon_option('priority')
        # if self._get_provider_option('regions'):
        #     data['regions'] = self._get_provider_option('regions')

        data['priority'] = 0

        for one_identifier in identifiers:
            self._patch('/{0}/zones/{1}/records/{2}'
                        .format(self.account_id, self.domain, one_identifier), data)
            LOGGER.debug('update_record: %s', one_identifier)

        LOGGER.debug('update_record: %s', True)
        return True

    # Delete an existing record.
    # If record does not exist, do nothing.
    def _delete_record(self, identifier=None, rtype=None, name=None, content=None):
        LOGGER.debug('in delete identifier=%s, rtype=%s, name=%s, content=%s' % (identifier, rtype,name, content) )

        return True

    # Helpers

    def _request(self, action='GET', url='/', data=None, query_params=None):
        if data is None:
            data = {}
        if query_params is None:
            query_params = {}
        default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'dddcurl / 7.61.0'
        }
        default_auth = None

        if self._get_provider_option('auth_token'):
            default_headers['Authorization'] = "Bearer {0}".format(
                self._get_provider_option('auth_token'))
        elif (self._get_provider_option('auth_username')
              and self._get_provider_option('auth_password')):
            default_auth = (self._get_provider_option(
                'auth_username'), self._get_provider_option('auth_password'))
        else:
            raise Exception('No valid authentication mechanism found for Checkdomain!!!!!')

        response = requests.request(action, self.api_endpoint + url, params=query_params,
                                    data=json.dumps(data),
                                    headers=default_headers,
                                    auth=default_auth)

        # for debugging
        self.PrintRequest(response, True)

        # if the request fails for any reason, throw an error.
        response.raise_for_status()
        LOGGER.debug("Check if we got data")

        if response.text is None:
            raise Exception('No data returned')

        # return the received body as json
        return response.json() if response.text else None

    def _patch(self, url='/', data=None, query_params=None):
        return self._request('PATCH', url, data=data, query_params=query_params)


    def _post(self, url='/', data=None, query_params=None):
        return self._request('POST', url, data=data, query_params=query_params)

    def PrintRequest(provider, response, print_text=False):
        """Print request details
           * request:    request object to examine
           * print_text: Print text content of request result"""

        print('--- URL ---')
        pprint.pprint(response.request.url)

        print('--- Status code ---')
        pprint.pprint(response.status_code)

        print('--- Request Headers ---')
        pprint.pprint(response.request.headers)

        print('--- Response Headers ---')
        pprint.pprint(response.headers)

        #        print('--- Cookies ---')
        #        pprint.pprint(response.request.cookies)

        if print_text:
            print('--- Content ---')
            pprint.pprint(response.text)

            print('--- JSON ---')
            pprint.pprint(response.json())

        print('--- History ---')
        pprint.pprint(response.history)

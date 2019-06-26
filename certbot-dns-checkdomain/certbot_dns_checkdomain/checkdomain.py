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
            'api_endpoint') or 'https://api.checkdomain.de'

        LOGGER.debug('check-domain module initialized....')



    def _authenticate(self):
        LOGGER.debug('IN: _authenticate')

        url = '/v1/domains?limit=100'
        next_url = url

        domains_found = []
        json_result = {}

        while next_url is not None:
            LOGGER.debug("in authenticate: Next-url %s" % ( next_url))

            response = self._get(next_url)
            json_result = response.json()

            if '_links' in json_result and 'next' in json_result['_links'] \
                    and 'href' in json_result['_links']['next']:
                next_url = json_result['_links']['next']['href']
            else:
                next_url = None

            # find our domain
            all_domains = json_result['_embedded']['domains']
            domains_found = [x for x in all_domains if x['name'] == self.domain]

            if (len(domains_found) > 0):
                break

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

        record = {
            'type': rtype,
            'name': self._relative_name(name),
            'value': content
        }

        record['ttl'] = 3600
        record['priority'] = 0

        response = self._post('/v1/domains/{0}/nameservers/records'.format(self.domain_id), record)
        # note: for post we get headers and no body
        location = response.headers['location']

        LOGGER.debug('in create_record: location=%s', location)

        idFromResponseLocationHeader = location.split("/")[-1]

        LOGGER.debug('in create_record: id in loaction = %s',  idFromResponseLocationHeader)
        return idFromResponseLocationHeader



    # List all records. Return an empty list if no records found
    # type, name and content are used to filter records.
    # If possible filter during the query, otherwise filter after response is received.
    def _list_records(self, rtype=None, name=None, content=None):
        LOGGER.debug('in: _list_records ---> rtype=%s, name=%s, content=%s' % (rtype,name, content) )

        url = '/v1/domains/{0}/nameservers/records?limit=100'.format(self.domain_id)

        records = []
        payload = {}

        next_url = url
        while next_url is not None:

            response = self._get(next_url)
            payload = response.json()

            # if '_links' in payload \
            #         and 'pages' in payload['_links'] \
            #         and 'next' in payload['_links']['pages']:
            #     next_url = payload['_links']['pages']['next']

            if '_links' in payload \
                    and 'next' in payload['_links'] \
                    and 'href' in payload['_links']['next']:
                next_url = payload['_links']['next']['href']

            else:
                next_url = None

            LOGGER.debug('in _list_records, next_url=%s' % (next_url) )

            for record in payload['_embedded']['records']:

                if '_links' in record:

                    href = record['_links']['self']['href']

                    link_id = href.split("/")[-1]

                    processed_record = {
                        'type': record['type'],
                        'name': "{0}.{1}".format(record['name'], self.domain),
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
                record for record in records if record['content'].lower() == content.lower()]

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

        data['ttl'] = 3600
        data['priority'] = 0

        #https://api.checkdomain.de/v1/domains/{domain}/nameservers/records/{record}
        for one_identifier in identifiers:
            response = self._put('/v1/domains/{0}/nameservers/records/{1}' .format(self.domain_id, one_identifier), data)
            one_identifier = response.json()
            LOGGER.debug('update_record: %s', one_identifier)

        LOGGER.debug('update_record: %s', True)
        return True



    # Delete an existing record.
    # If record does not exist, do nothing.
    # for checkDomain, we can't delete rec so return true
    def _delete_record(self, identifier=None, rtype=None, name=None, content=None):
        #LOGGER.debug('in delete identifier=%s, rtype=%s, name=%s, content=%s' % (identifier, rtype,name, content) )
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
        # return response.json() if response.text else None

        # return the response
        return response



    def _put(self, url='/', data=None, query_params=None):
        return self._request('PUT', url, data=data, query_params=query_params)



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

            try:
                print('--- JSON ---')
                pprint.pprint(response.json())
            except:
                print("Something went wrong printing response.json()")

        print('--- response History ---')
        pprint.pprint(response.history)

"""DNS Authenticator for CheckDomain DNS."""
import logging

import zope.interface
#from lexicon.providers import checkdomain

from certbot_dns_checkdomain.checkdomain import Provider

from certbot import errors
from certbot import interfaces
from certbot.plugins import dns_common
from certbot.plugins import dns_common_lexicon

logger = logging.getLogger(__name__)



# currently playing with the code (copied from checkdmainOriginal.py)

@zope.interface.implementer(interfaces.IAuthenticator)
@zope.interface.provider(interfaces.IPluginFactory)
class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for CheckDomain

    This Authenticator uses the CheckDomain v1 API to fulfill a dns-01 challenge.
    """

    description = 'Obtain certificates using a DNS TXT record (if you are using CheckDomain for DNS).'
    ttl = 60

    def __init__(self, *args, **kwargs):
        super(Authenticator, self).__init__(*args, **kwargs)
        self.credentials = None

    @classmethod
    def add_parser_arguments(cls, add):  # pylint: disable=arguments-differ
        super(Authenticator, cls).add_parser_arguments(add, default_propagation_seconds=30)
        add('credentials', help='CheckDomain credentials INI file.')

    def more_info(self):  # pylint: disable=missing-docstring,no-self-use
        return 'This plugin configures a DNS TXT record to respond to a dns-01 challenge using ' + \
               'the CheckDomain API.'

    def _setup_credentials(self):
        self.credentials = self._configure_credentials(
            'credentials',
            'CheckDomain credentials INI file',
            {
                'token': 'User access token for CheckDomain v1 API. '
            }
        )

    def _perform(self, domain, validation_name, validation):
        self._get_checkdomain_client().add_txt_record(domain, validation_name, validation)

    def _cleanup(self, domain, validation_name, validation):
        self._get_checkdomain_client().del_txt_record(domain, validation_name, validation)

    def _get_checkdomain_client(self):
        return _CheckDomainLexiconClient(self.credentials.conf('token'), self.ttl)


class _CheckDomainLexiconClient(dns_common_lexicon.LexiconClient):
    """
    Encapsulates all communication with the CheckDomain via Lexicon.
    """

    def __init__(self, token, ttl):
        super(_CheckDomainLexiconClient, self).__init__()

        config = dns_common_lexicon.build_lexicon_config('checkdomain', {
            'ttl': ttl,
        }, {
            'auth_token': token,
        })

        self.provider = Provider(config)

    def _handle_http_error(self, e, domain_name):
        hint = None
        if str(e).startswith('401 Client Error: Unauthorized for url:'):
            hint = 'Is your API token value correct?'

        return errors.PluginError('Error determining zone identifier for {0}: {1}.{2}'
                                  .format(domain_name, e, ' ({0})'.format(hint) if hint else ''))

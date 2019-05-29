"""Tests for certbot_dns_checkdomain.dns_checkdomain."""

import unittest

import mock
from requests.exceptions import HTTPError

from certbot.compat import os
from certbot.plugins import dns_test_common
from certbot.plugins import dns_test_common_lexicon
from certbot.tests import util as test_util

TOKEN = 'foo'


class AuthenticatorTest(test_util.TempDirTestCase,
                        dns_test_common_lexicon.BaseLexiconAuthenticatorTest):

    def setUp(self):
        super(AuthenticatorTest, self).setUp()

        from certbot_dns_checkdomain.dns_checkdomain import Authenticator

        #path = os.path.join(self.tempdir, 'file.ini')
        path = os.path.join(self.tempdir, '/tmp/xxx/authorization_key.ini')
        dns_test_common.write({"checkdomain_token": TOKEN}, path)

        self.config = mock.MagicMock(checkdomain_credentials=path,
                                     checkdomain_propagation_seconds=0)  # don't wait during tests

        self.auth = Authenticator(self.config, "checkdomain")

        self.mock_client = mock.MagicMock()
        # _get_checkdomain_client | pylint: disable=protected-access
        self.auth._get_checkdomain_client = mock.MagicMock(return_value=self.mock_client)


class CheckDomainLexiconClientTest(unittest.TestCase, dns_test_common_lexicon.BaseLexiconClientTest):

    LOGIN_ERROR = HTTPError('401 Client Error: Unauthorized for url: ...')

    def setUp(self):
        from certbot_dns_checkdomain.dns_checkdomain import _CheckDomainLexiconClient

        self.client = _CheckDomainLexiconClient(TOKEN, 0)

        self.provider_mock = mock.MagicMock()
        self.client.provider = self.provider_mock


if __name__ == "__main__":
    unittest.main()  # pragma: no cover

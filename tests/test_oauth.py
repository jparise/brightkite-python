#!/usr/bin/python

import unittest
import brightkite
import oauth.oauth as oauth

username = None
consumer_key = None
consumer_secret = None
access_key = None
access_secret = None

class TestOAuth(unittest.TestCase):
    """Test the OAuth authentication interface"""

    def runTest(self):
        token = oauth.OAuthToken(access_key, access_secret)
        auth = brightkite.OAuth(consumer_key, consumer_secret, token)
        api = brightkite.Brightkite(auth)
        self.assertEqual(api.me().login, username)

if __name__ == '__main__':
    username = raw_input('Brightkite username: ')
    consumer_key = raw_input('OAuth consumer key: ')
    consumer_secret = raw_input('OAuth consumer secret: ')
    access_key = raw_input('OAuth access key: ')
    access_secret = raw_input('OAuth access secret: ')
    unittest.main()

#!/usr/bin/python

import unittest
import brightkite

username = None
password = None

PLACE_UUID  = '8fde23d6245c11debf73003048c0801e' # Brightkite (Burlingame)
OBJECT_UUID = 'c09617edc7ff700faf66ec71a7646b2506e20035' # Moscone Center

class TestBrightkite(unittest.TestCase):
    """Test the basic Brightkite API"""

    def setUp(self):
        auth = brightkite.BasicAuth(username, password)
        self.api = brightkite.Brightkite(auth)

    def tearDown(self):
        self.api = None

    def test_me(self):
        o = self.api.me()
        self.assertEqual(o.login, username)

    def test_person(self):
        o = self.api.person(username)
        self.assertEqual(o.login, username)

    def test_people(self):
        l = self.api.people('parise')
        self.assertTrue(len(l) >= 1)
        self.assertTrue(locate(l, lambda o: o.login == 'jparise'))

    def test_friends(self):
        l = self.api.friends('jparise')
        self.assertTrue(len(l) >= 1)
        self.assertTrue(locate(l, lambda o: o.login == 'Brightkite'))

    def test_object(self):
        o = self.api.object(OBJECT_UUID)
        self.assertEqual(o.uuid, OBJECT_UUID)
        self.assertTrue('place' in o.keys())
        self.assertEqual(o.place['name'], 'Moscone Center')

    def test_objects(self):
        l = self.api.objects('Burlingame')
        self.assertTrue(len(l) >= 1)
        self.assertTrue(locate(l, lambda o: o.place['name'] == 'Brightkite'))

    def test_place(self):
        o = self.api.place(PLACE_UUID)
        self.assertEqual(o.uuid, PLACE_UUID)
        self.assertEqual(o.name, 'Brightkite')

    def test_places(self):
        l = self.api.places('Burlingame, CA')
        self.assertTrue(len(l) >= 1)
        self.assertTrue(locate(l, lambda o: o.name == 'Burlingame'))

    def test_placemarks(self):
        l = self.api.placemarks()
        self.assertTrue(len(l) >= 0)

    def test_config(self):
        o = self.api.config()
        self.assertEqual(o.login, username)

def locate(l, pred):
    """Attempt to locate an entry in a sequence using the given predicate."""
    for o in l:
        if pred(o):
            return o
    return None

if __name__ == '__main__':
    from getpass import getpass
    username = raw_input('Brightkite username: ')
    password = getpass('Brightkite password: ')
    unittest.main()

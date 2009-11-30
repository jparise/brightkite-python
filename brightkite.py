# Brightkite API Library
# http://groups.google.com/group/brightkite-api/web/rest-api

import json
import urllib

__author__  = 'Jon Parise <jon@indelible.org>'
__version__ = '0.9.0'

__all__ = ['Brightkite']

class AuthenticatingOpener(urllib.FancyURLopener):
    __slots__ = ('user', 'password')

    def __init__(self, user, password):
        urllib.FancyURLopener.__init__(self)
        self.user = user
        self.password = password

    def prompt_user_passwd(self, host, realm):
        return (self.user, self.password)


class Brightkite:

    def __init__(self, user, password):
        self.opener = AuthenticatingOpener(user, password)

    def _get(self, uri):
        url = 'http://brightkite.com/' + uri
        return json.load(self.opener.open(url))

    def _post(self, uri, data):
        url = 'http://brightkite.com/' + uri
        return json.load(self.opener.open(url, data))

    def me(self, raw=False):
        d = self._get('me.json')
        if raw: return d
        return BrightkitePerson(self, d['id'], d)

    def person(self, user, raw=False):
        d = self._get('people/' + user + '.json')
        if raw: return d
        return BrightkitePerson(self, d['id'], d)

    def people(self, query, raw=False):
        l = self._get('people/search.json?query=' + query)
        if raw: return l
        return [BrightkitePerson(self, d['id'], d) for d in l]

    def friends(self, user, pending=False, raw=False):
        if pending:
            l = self._get('people/' + user + '/pending_friends.json')
        else:
            l = self._get('people/' + user + '/friends.json')
        if raw: return l
        return [BrightkitePerson(self, d['id'], d) for d in l]

    def object(self, uuid, raw=False):
        d = self._get('objects/' + uuid + '.json')
        if raw: return d
        return BrightkiteObject(self, uuid, d)

    def objects(self, query, raw=False):
        l = self._get('objects/search.json?oquery=' + query)
        if raw: return l
        if type(l) is not list: l = [l]
        return [BrightkiteObject(self, d['id'], d) for d in l]

    def place(self, uuid, raw=False):
        d = self._get('places/' + uuid + '.json')
        if raw: return d
        return BrightkitePlace(self, uuid, d)

    def place_objects(self, uuid, raw=False):
        l = self._get('places/' + uuid + '/objects.json')
        if raw: return l
        return [BrightkiteObject(self, d['id'], d) for d in l]

    def place_people(self, uuid, radius=None, hours_ago=None, raw=False):
        params = {}
        if radius is not None:
            params['radius'] = radius
        if hours_ago is not None:
            params['hours_ago'] = hours_ago
        uri = 'places/' + uuid + '/people.json' + urllib.urlencode(params)
        l = self._get(uri)
        if raw: return l
        return [BrightkitePerson(self, d['id'], d) for d in l]

    def places(self, query, raw=False):
        l = self._get('places/search.json?q=' + query)
        if raw: return l
        if type(l) is not list: l = [l]
        return [BrightkitePlace(self, d['id'], d) for d in l]

    def placemarks(self, raw=False):
        l = self._get('me/placemarks.json')
        if raw: return l
        return [BrightkitePlace(self, d['id'], d) for d in l]

class BrightkiteObject(object):

    def __init__(self, api, uuid, d=None):
        self.api = api
        self.uuid = uuid
        self.d = d or dict()

    def __repr__(self):
        return '<%s uuid=%s>' % (self.__class__.__name__, self.uuid)

    def __getattr__(self, name):
        try:
            return self.d[name]
        except KeyError:
            raise AttributeError("invalid property '%s'" % name)

    def keys(self):
        return self.d.keys()

class BrightkiteQueryObject(BrightkiteObject):

    def _query(self, uri, checkins=False, notes=False, photos=False, raw=False):
        filters = []
        if checkins: filters.append('checkins')
        if notes: filters.append('notes')
        if photos: filters.append('photos')

        if filters:
            uri += '?' + ','.join(filters)

        l = self.api._get(uri)
        if raw: return l
        return [BrightkiteObject(self, d['id'], d) for d in l]

    def objects(self, checkins=False, notes=False, photos=False, raw=False):
        raise NotImplementedError

    def checkins(self, raw=False):
        return self.objects(checkins=True, raw=raw)

    def notes(self, raw=False):
        return self.objects(notes=True, raw=raw)

    def photos(self, raw=False):
        return self.objects(photos=True, raw=raw)

class BrightkitePerson(BrightkiteQueryObject):

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.login)

    def objects(self, checkins=False, notes=False, photos=False, raw=False):
        uri = 'people/' + self.login + '/objects.json'
        return self._query(uri, checkins, notes, photos, raw=raw)

class BrightkitePlace(BrightkiteQueryObject):

    def objects(self, checkins=False, notes=False, photos=False, raw=False):
        uri = 'places/' + self.uuid + '/objects.json'
        return self._query(uri, checkins, notes, photos, raw=raw)

    def placemarks(self, raw=False):
        l = self.api._get('places/' + self.uuid + '/placemarks.json')
        if raw: return l
        return [BrightkitePlace(self, d['id'], d) for d in l]

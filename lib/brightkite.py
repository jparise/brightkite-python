# Brightkite API Library
# http://groups.google.com/group/brightkite-api/web/rest-api

import base64
import httplib
import json
import urllib

__author__  = 'Jon Parise <jon@indelible.org>'
__version__ = '0.9.0'

__all__ = ['Brightkite', 'Object', 'Person', 'Place', 'Config']

SERVER = 'brightkite.com'


class BrightkiteException(Exception):
    pass

class BrightkiteHTTPException(BrightkiteException):

    def __init__(self, url, code, msg):
        self.url = method
        self.code = code
        self.msg = msg

    def __str__(self):
        return "HTTP {0}: {1} ({2})".format(self.url, self.code, self.msg)


class NullAuth(object):
    """No Authentication"""

    def prepare(self, headers):
        pass

class BasicAuth(object):
    """HTTP Basic Authentication"""

    __slots__ = ['username', 'password']

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def prepare(self, headers):
        s = base64.encodestring('%s:%s' % (self.username, self.password))[:-1]
        headers['Authorization'] = 'Basic ' + s


class Brightkite(object):

    def __init__(self, username, password, server=None):
        if server is None:
            server = SERVER
        self.http = httplib.HTTPConnection(server)
        self.auth = BasicAuth(username, password)

    def _request(self, method, url, body=None, headers=None):
        """Send an HTTP request and read the response data."""
        if headers is None:
            headers = dict()

        self.auth.prepare(headers)

        self.http.request(method, url, body, headers)
        response = self.http.getresponse()
        data = response.read()

        if response.status != 200:
            raise BrightkiteHTTPException(url, response.status, data)

        return data

    def _get(self, uri):
        url = 'http://brightkite.com/' + uri
        data = self._request('GET', url)
        return json.loads(data)

    def _post(self, uri, data):
        url = 'http://brightkite.com/' + uri
        data = self._request('POST', url)
        return json.loads(data)

    def _put(self, uri, key, value):
        pass

    def me(self, raw=False):
        d = self._get('me.json')
        if raw: return d
        return Person(self, d['id'], d)

    def person(self, user, raw=False):
        d = self._get('people/' + urllib.quote(user) + '.json')
        if raw: return d
        return Person(self, d['id'], d)

    def people(self, query, raw=False):
        l = self._get('people/search.json?query=' + urllib.quote(query))
        if raw: return l
        return [Person(self, d['id'], d) for d in l]

    def friends(self, user, pending=False, raw=False):
        user = urllib.quote(user)
        if pending:
            l = self._get('people/' + user + '/pending_friends.json')
        else:
            l = self._get('people/' + user + '/friends.json')
        if raw: return l
        return [Person(self, d['id'], d) for d in l]

    def object(self, uuid, raw=False):
        d = self._get('objects/' + urllib.quote(uuid) + '.json')
        if raw: return d
        return Object(self, uuid, d)

    def objects(self, query, raw=False):
        l = self._get('objects/search.json?oquery=' + urllib.quote(query))
        if raw: return l
        if type(l) is not list: l = [l]
        return [Object(self, d['id'], d) for d in l]

    def place(self, uuid, raw=False):
        d = self._get('places/' + urllib.quote(uuid) + '.json')
        if raw: return d
        return Place(self, uuid, d)

    def places(self, query, raw=False):
        l = self._get('places/search.json?q=' + urllib.quote(query))
        if raw: return l
        if type(l) is not list: l = [l]
        return [Place(self, d['id'], d) for d in l]

    def placemarks(self, raw=False):
        l = self._get('me/placemarks.json')
        if raw: return l
        return [Place(self, d['id'], d) for d in l]

    def sent_messages(self):
        return self._get('me/sent_messages.json')

    def received_messages(self):
        return self._get('me/received_messages.json')

    def config(self, raw=False):
        d = self._get('me/config.json')
        if raw: return d
        return Config(self, d)

class Object(object):

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

class QueryObject(Object):

    def _query(self, uri, checkins=False, notes=False, photos=False, raw=False):
        filters = []
        if checkins: filters.append('checkins')
        if notes: filters.append('notes')
        if photos: filters.append('photos')

        if filters:
            uri += '?' + ','.join(filters)

        l = self.api._get(uri)
        if raw: return l
        return [Object(self, d['id'], d) for d in l]

    def objects(self, checkins=False, notes=False, photos=False, raw=False):
        raise NotImplementedError

    def checkins(self, raw=False):
        return self.objects(checkins=True, raw=raw)

    def notes(self, raw=False):
        return self.objects(notes=True, raw=raw)

    def photos(self, raw=False):
        return self.objects(photos=True, raw=raw)

class Person(QueryObject):

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.login)

    def objects(self, checkins=False, notes=False, photos=False, raw=False):
        uri = 'people/' + urllib.quote(self.login) + '/objects.json'
        return self._query(uri, checkins, notes, photos, raw=raw)

    def friendship(self):
        uri = 'people/' + urllib.quote(self.login) + '/friendship.json'
        return self.api._get(uri)

class Place(QueryObject):

    def objects(self, checkins=False, notes=False, photos=False, raw=False):
        uri = 'places/' + urllib.quote(self.uuid) + '/objects.json'
        return self._query(uri, checkins, notes, photos, raw=raw)

    def people(self, radius=None, hours_ago=None, raw=False):
        uri = 'places/' + urlib.quote(self.uuid) + '/people.json'
        params = {}
        if radius is not None:
            params['radius'] = radius
        if hours_ago is not None:
            params['hours_ago'] = hours_ago
        uri += urllib.urlencode(params)
        l = self.api._get(uri)
        if raw: return l
        return [Person(self, d['id'], d) for d in l]

    def placemarks(self, raw=False):
        uri = 'places/' + urllib.quote(self.uuid) + '/placemarks.json'
        l = self.api._get(uri)
        if raw: return l
        return [Place(self, d['id'], d) for d in l]

class Config(object):

    def __init__(self, api, d=None):
        self.api = api
        self.d = d or dict()

    def __repr__(self):
        return '<%s login=%s>' % (self.__class__.__name__, self.login)

    def __getattr__(self, name):
        try:
            return self.d[name]
        except KeyError:
            raise AttributeError("invalid setting '%s'" % name)

    def __setattr__(self, name, value):
        if name == 'api' or name == 'd':
            object.__setattr__(self, name, value)
        elif name in self.d:
            # TODO: Send the HTTP PUT request
            self.d[name] = value
        else:
            raise AttributeError("invalid setting '%s'" % name)

    def keys(self):
        return self.d.keys()

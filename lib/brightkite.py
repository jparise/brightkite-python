# Brightkite API Library
# http://groups.google.com/group/brightkite-api/web/rest-api

import base64
import httplib
import json
import urllib

# The oauth module is optional (but recommended).  Attempting to use the
# OAuth authentication class below when the oauth module is unavailable will
# result in an immediate error.
try:
    import oauth.oauth as oauth
except:
    pass

__author__  = 'Jon Parise <jon@indelible.org>'
__version__ = '0.9.0'

__all__ = ['Brightkite', 'Object', 'Person', 'Place', 'Config',
           'BasicAuth', 'OAuth']

SERVER = 'apps.brightkite.com'


class BrightkiteException(Exception):
    pass

class BrightkiteHTTPException(BrightkiteException):

    def __init__(self, url, code, msg):
        self.url = url
        self.code = code
        self.msg = msg

    def __str__(self):
        return "HTTP {0}: {1} ({2})".format(self.url, self.code, self.msg)


class BasicAuth(object):
    """HTTP Basic Authentication"""

    __slots__ = ['username', 'password']

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def prepare(self, method, url, params, token=None):
        query = urllib.urlencode(params)
        body = query if method in ('POST', 'PUT') else None
        if len(query):
            url += '?' + query
        s = base64.encodestring('%s:%s' % (self.username, self.password))[:-1]
        return url, body, {'Authorization': 'Basic ' + s}

class OAuth(object):
    """OAuth Authentication"""

    def __init__(self, key, secret, access_token=None):
        self.key = key
        self.consumer = oauth.OAuthConsumer(key, secret)
        self.signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
        self.access_token = access_token

    def prepare(self, method, url, params, token=None):
        if token is None:
            token = self.access_token

        request = oauth.OAuthRequest.from_consumer_and_token(
                self.consumer,
                token=token,
                http_method=method,
                http_url=url,
                parameters=params)
        request.sign_request(self.signature_method, self.consumer, token)

        if method == 'GET':
            url = request.to_url()

        body = None
        if method in ('POST', 'PUT'):
            body = request.to_postdata()

        return url, body, {}


class Brightkite(object):
    """Brightkite API"""

    def __init__(self, auth, server=None, secure=True, debug=False):
        if server is None:
            server = SERVER

        self.auth = auth

        if secure:
            self.http = httplib.HTTPSConnection(server)
            self.urlbase = 'https://' + server + '/'
        else:
            self.http = httplib.HTTPConnection(server)
            self.urlbase = 'http://' + server + '/'

        if debug:
            self.http.set_debuglevel(1)

    def _request(self, method, url, params=None, token=None):
        """Send an HTTP request and read the response data."""
        if params is None:
            params = {}

        # Prepare the request by passing it through our authentication object.
        # This will build the final URL (including encoding query parameters),
        # POST body data, and HTTP headers.
        url, body, headers = self.auth.prepare(method, url, params, token)

        # If we have some POST body data, we need to set a few more HTTP
        # headers in order for the request to be processed correctly.
        if body is not None:
            headers['Content-type'] = 'application/x-www-form-urlencoded'
            headers['Accept'] = 'text/plain'

        # Issue the request and read the complete contents of the response.
        # httplib requires us to drain the response data before we can issue
        # another request.
        self.http.request(method, url, body, headers)
        response = self.http.getresponse()
        data = response.read()

        # If we received anything other than a successful response, raise an
        # exception to the caller and bail.  There's nothing more we can do.
        if response.status != 200:
            raise BrightkiteHTTPException(url, response.status, data)

        return data

    def _get(self, uri, params=None):
        data = self._request('GET', self.urlbase + uri, params)
        return json.loads(data)

    def _post(self, uri, params=None):
        data = self._request('POST', self.urlbase + uri, params)
        return json.loads(data)

    def _put(self, uri, params=None):
        self._request('PUT', self.urlbase + uri, params)

    def oauth_request_token(self):
        if not isinstance(self.auth, OAuth):
            raise BrightkiteException('requires OAuth authentication')
        data = self._request('GET', self.urlbase + 'oauth/request_token')
        return oauth.OAuthToken.from_string(data)

    def oauth_authorize(self, token):
        if not isinstance(self.auth, OAuth):
            raise BrightkiteException('requires OAuth authentication')
        # Because we just want the authorization URL, we don't need to issue
        # an actual HTTP request.  We can return the prepared URL directly.
        url = self.urlbase + 'oauth/authorize'
        return self.auth.prepare('GET', url, {}, token)[0]

    def oauth_access_token(self, token):
        if not isinstance(self.auth, OAuth):
            raise BrightkiteException('requires OAuth authentication')
        url = self.urlbase + 'oauth/access_token'
        data = self._request('GET', url, token=token)
        return oauth.OAuthToken.from_string(data)

    def me(self, raw=False):
        d = self._get('me.json')
        if raw: return d
        return Person(self, d['id'], d)

    def person(self, user, raw=False):
        d = self._get('people/' + urllib.quote(user) + '.json')
        if raw: return d
        return Person(self, d['id'], d)

    def people(self, query, raw=False):
        l = self._get('people/search.json', {'query': query})
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
        l = self._get('objects/search.json', {'oquery': query})
        if raw: return l
        if type(l) is not list: l = [l]
        return [Object(self, d['id'], d) for d in l]

    def place(self, uuid, raw=False):
        d = self._get('places/' + urllib.quote(uuid) + '.json')
        if raw: return d
        return Place(self, uuid, d)

    def places(self, query, raw=False):
        l = self._get('places/search.json', {'q': query})
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

        params = {}
        if filters:
            params['filters'] = ','.join(filters)

        l = self.api._get(uri, params)
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
        l = self.api._get(uri, params)
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
            self.api._put('me/config.json', {'person[' + name + ']': value})
            self.d[name] = value
        else:
            raise AttributeError("invalid setting '%s'" % name)

    def keys(self):
        return self.d.keys()

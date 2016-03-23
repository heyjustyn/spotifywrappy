import requests
import datetime
import base64
import json
import calendar

class SpotifyException(Exception):
    def __init__(self, http_status, code, msg):
        self.http_status = http_status
        self.code = code
        self.msg = msg

    def __str__(self):
        return 'http status: {0}, code:{1} - {2}'.format(
            self.http_status, self.code, self.msg)

class Spotify(object):
    spotify_auth_url = 'https://accounts.spotify.com'
    spotify_client_auth_path = '/authorize/?client_id={0}&response_type=code&redirect_uri={1}&scope={2}'
    spotify_api_url = 'https://api.spotify.com'

    VERBOSE = False

    def __init__(self, client_id, client_secret, redirect_uri, scope):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.client_auth_url = self.spotify_auth_url + self.spotify_client_auth_path.format(client_id, redirect_uri, scope)
        self.access_token = None


    def _request(self, method, url, headers, isJsonContent, params=None, data=None):
        if self.access_token is not None and self._get_current_utc_ts() > self.expires_in:
            self._refresh_token()
        if headers is not None and isJsonContent is True:
            headers['Content-Type'] = 'application/json'
        session = requests.Session()
        request = session.request(method, url, headers=headers, params=params, data=data)
        if self.VERBOSE:
            print("REQUEST")
            print(method, request.status_code, request.url)
            if params:
                print("PARAMS", json.dumps(params))
            if data:
                print("DATA", json.dumps(data))
            print()
        request.connection.close()
        return request

    def _get(self, url, params=None, headers=None, isJsonContent=True):
        return self._request(method="GET", url=url, headers=headers, params=params, isJsonContent=isJsonContent)

    def _post(self, url, data=None, headers=None, isJsonContent=True):
        return self._request(method="POST", url=url, headers=headers, data=data, isJsonContent=isJsonContent)

    def _get_current_utc_ts(self):
        return calendar.timegm(datetime.datetime.utcnow().utctimetuple())

    """
        Authorization Code Flow
        https://developer.spotify.com/web-api/authorization-guide/#authorization-code-flow
    """

    def _refresh_token(self):
        url = self.spotify_auth_url + '/api/token'
        authValue = self.client_id + ":" + self.client_secret
        headers = {'Authorization' : "Basic " + base64.b64encode(authValue.encode()).decode()}
        data = {
            'grant_type' : "refresh_token",
            'refresh_token' : self.refresh_token
        }

        response = self._post(url=url, headers=headers, data=data, isJsonContent=False)
        if response.status_code is 200:
            body = response.json()
            self.access_token = body["access_token"]
            self.expires_in = self._get_current_utc_ts() + body["expires_in"]
        else:
            raise SpotifyException(response.status_code, response.url, "Spotify authorization failed when refreshing token")


    def authorize(self, code):
        """Completes step 4 & 5 (gets your access token by using the code that is returned from step 3) of Authorization Code Flow
        """
        url = self.spotify_auth_url + '/api/token'
        data = {
            'grant_type' : "authorization_code",
            'code' : code,
            'redirect_uri' : self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        response = self._post(url=url, data=data, isJsonContent=False)
        if response.status_code is 200:
            body = response.json()
            self.access_token = body["access_token"]
            self.refresh_token = body["refresh_token"]
            self.expires_in = self._get_current_utc_ts() + body["expires_in"]
        else:
            raise SpotifyException(response.status_code, response.url, "Spotify Authorization Failed")

    """
        Albums Endpoints
        https://developer.spotify.com/web-api/album-endpoints/
    """

    def get_album(self, id, market=None):
        url = self.spotify_api_url + "/v1/albums/{0}".format(id)
        response = self._get(url=url)
        if response.status_code is 200:
            return response.json()
        else:
            raise SpotifyException(response.status_code, response.url, response.json()['error']['message'])

    """
        Artists Endpoints
        https://developer.spotify.com/web-api/artist-endpoints/
    """

    def artist_top_tracks(self, id, country):
        """Get Spotify catalog information about an artist’s top tracks by country.
        https://developer.spotify.com/web-api/get-artists-top-tracks/
        """
        url = self.spotify_api_url + "/v1/artists/{0}/top-tracks".format(id)
        params = { 'country' : country}

        response = self._get(url=url, params=params)
        if response.status_code is 200:
            return response.json()
        else:
            raise SpotifyException(response.status_code, response.url, response.json()['error']['message'])

    """
        Browse Endpoints
        https://developer.spotify.com/web-api/browse-endpoints/
    """

    """
        Follow Endpoints
        https://developer.spotify.com/web-api/web-api-follow-endpoints/
    """

    """
        “Your Music” Library Endpoints
        https://developer.spotify.com/web-api/library-endpoints/
    """

    """
        Playlist Endpoints
        https://developer.spotify.com/web-api/playlist-endpoints/
    """

    def create_playlist(self, userId, name, public=True):
        """Create a playlist for a Spotify user. (The playlist will be empty until you add tracks.)
        https://developer.spotify.com/web-api/create-playlist/
        """
        url = self.spotify_api_url + "/v1/users/{0}/playlists".format(userId)
        headers = { 'Authorization' : "Bearer  %s" % self.access_token }
        data = {
            'name' : name,
            'public' : public
        }

        response = self._post(url=url, headers=headers, data=json.dumps(data))
        if response.status_code in [200, 201]:
            return response.json()
        elif response.status_code is 403:
            raise SpotifyException(response.status_code, response.url, "Insufficient scope permission")
        else:
            raise SpotifyException(response.status_code, response.url, response.json()['error']['message'])

    def add_tracks_to_playlist(self, userId, playlistId, uris):
        """Add one or more tracks to a user’s playlist.
        https://developer.spotify.com/web-api/add-tracks-to-playlist/
        """
        url = self.spotify_api_url + "/v1/users/{0}/playlists/{1}/tracks".format(userId, playlistId)
        headers = { 'Authorization' : "Bearer  %s" % self.access_token }
        data = { 'uris' : uris }

        response = self._post(url=url, headers=headers, data=json.dumps(data))
        if response.status_code is 201:
            return response.json()
        elif response.status_code is 403:
            raise SpotifyException(response.status_code, response.url, "Insufficient scope permission")
        else:
            raise SpotifyException(response.status_code, response.url, response.json()['error']['message'])

    """
        User Profile Endpoints
        https://developer.spotify.com/web-api/user-profile-endpoints/
    """

    def me(self):
        """Get detailed profile information about the current user (including the current user’s username).
        https://developer.spotify.com/web-api/get-current-users-profile/
        """
        url = self.spotify_api_url + '/v1/me'
        headers = {'Authorization' : "Bearer  %s" % self.access_token}

        response = self._get(url=url, headers=headers)
        if response.status_code is 200:
            return response.json()
        elif response.status_code is 403:
            raise SpotifyException(response.status_code, response.url, "Insufficient scope permission")
        else:
            raise SpotifyException(response.status_code, response.url, response.json()['error']['message'])

    """
        Search Endpoint
        https://developer.spotify.com/web-api/search-item/
    """

    def search(self, q, type, market=None, limit=20, offset=0):
        """Get Spotify catalog information about artists, albums, tracks or playlists that match a keyword string.
        https://developer.spotify.com/web-api/search-item/
        """
        url = self.spotify_api_url + '/v1/search'
        headers = { 'Authorization': "Bearer  %s" % self.access_token }
        params = {
            'q' : q.encode('utf-8'),
            'type' : type,
            'market' : market,
            'limit' : limit,
            'offset' : offset
        }

        response = self._get(url=url, headers=headers, params=params)
        if response.status_code is 200:
            return response.json()
        else:
            raise SpotifyException(response.status_code, response.url, response.json()['error']['message'])

    """
        Track Endpoints Endpoints
        https://developer.spotify.com/web-api/track-endpoints/
    """

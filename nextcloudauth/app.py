from requests_oauthlib import OAuth2Session
from flask import Flask, request, jsonify, session, abort, redirect
import os, json

class Application(object):

    def __init__(self, name, settings):
        self.name = name
        self.access_token_url = settings['access_token_url']
        self.authorize_url = settings['authorize_url']

        self.client_id = settings['client_id']
        self.client_secret = settings['client_secret']
        self.scopes = settings.get('scopes', [])
        self.redirect_url = settings['redirect_url']

    def get_cookie(self, cookie):
        return '{0}_{1}'.format(self.name, cookie)

    def get_authorization_url(self):
        session = OAuth2Session(self.client_id, redirect_uri=self.redirect_url, scope=self.scopes)
        return session.authorization_url(self.authorize_url)

    def fetch_token(self, state, url):
        url = url.replace('http://', 'https://')
        session = OAuth2Session(client_id=self.client_id, state=state, redirect_uri=self.redirect_url)

        return session.fetch_token(self.access_token_url, client_secret=self.client_secret, authorization_response=url)

environ_path = os.path.join('..', 'settings.json')

with open(environ_path, 'r') as f:
    settings = json.load(f)

app = Flask(__name__)
app.secret_key = settings['secret_key']

APPS = {}

for app_name, app_config in settings['applications'].items():
    APPS[app_name] = Application(app_name, app_config)

def get_application(app_name):
    return APPS.get(app_name)

@app.route('/<name>')
def oauth_request(name):
    app = get_application(name)

    if not app:
        abort(404, 'Unknown application.')

    authorization_url, state = app.get_authorization_url()
    session[app.get_cookie('state')] = state
    return redirect(authorization_url)

@app.route('/<name>/authorized')
def authorized(name):
    app = get_application(name)

    if not app:
        abort(404, 'Unknown application.')

    if 'state' not in request.args:
        abort(403, 'Invalid authorization request.')

    state = str(request.args['state'])

    if session.pop(app.get_cookie('state'), None) != state:
        abort(403, 'No authorization request is currently in progress.')

    return jsonify(app.fetch_token(state, request.url))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
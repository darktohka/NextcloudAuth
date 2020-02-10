
from requests-oauthlib import OAuth
from flask import Flask, request, jsonify, session, abort
import os, sys, uuid, json

class Application(object):

    def __init__(self, oauth, name, settings):
        self.oauth = oauth
        self.name = name
        self.base_url = settings['base_url']
        self.access_token_url = settings['access_token_url']
        self.authorize_url = settings['authorize_url']

        self.client_id = settings['client_id']
        self.client_secret = settings['client_secret']
        self.extra = settings.get('extra', {})
        self.redirect_url = settings['redirect_url']

        self.app = None

    def get_cookie(self, cookie):
        return '{0}_{1}'.format(self.name, cookie)

    def get(self):
        if not self.app:
            self.app = self.oauth.remote_app(self.name,
                access_token_url=self.access_token_url, authorize_url=self.authorize_url,
                consumer_key=self.client_id, consumer_secret=self.client_secret,
                request_token_params=self.extra,
                request_token_url=None, access_token_method='POST',
                base_url=self.base_url
            )

        return self.app

environ_path = os.path.join('..', 'settings.json')

with open(environ_path, 'r') as f:
    settings = json.load(f)

app = Flask(__name__)
app.secret_key = 'hahahaha'

oauth = OAuth(app,)
APPS = {}

for app_name, app_config in settings['applications'].items():
    APPS[app_name] = Application(oauth, app_name, app_config)

def get_application(app_name):
    return APPS.get(app_name)

@app.route('/<name>')
def oauth_request(name):
    app = get_application(name)

    if not app:
        abort(404, 'Unknown application.')

    state = app.get_cookie('state')
    session[state] = str(uuid.uuid4())
    return app.get().authorize(callback=app.redirect_url, state=session[state])

@app.route('/<name>/authorized')
def authorized(name):
    app = get_application(name)

    if not app:
        abort(404, 'Unknown application.')

    state = app.get_cookie('state')

    if 'state' not in request.args or str(session.pop(state, None)) != str(request.args['state']):
        abort(403, 'No authorization request is currently in progress.')

    return jsonify(app.get().authorized_response())

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
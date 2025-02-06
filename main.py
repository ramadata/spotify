from datetime import datetime
import os
from dotenv import load_dotenv
from requests import post, get
import json
from urllib.parse import urlencode
from flask import Flask, session, request, redirect, jsonify 

load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")
scope = os.getenv("SCOPE")
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = 'https://api.spotify.com/v1/'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

@app.route('/')
def index():
    return "Welcome to my Spotify App <a href='/login'> Login with Spotify </a>"

@app.route('/login')
def login():
    scope = 'user-read-private user-read-email'

    auth_params = {
        'response_type': 'code',
        'client_id': client_id,
        'scope': scope,
        'redirect_uri': redirect_uri,
        'show_dialog': True
    }
    auth_url = f"{AUTH_URL}?{urlencode(auth_params)}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    if 'code' in request.args:

        token_data = {
            'grant_type': 'authorization_code',
            'code': request.args['code'],
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret
        }

        response = post(TOKEN_URL, data=token_data)
        token_info = response.json()

    if 'access_token' in token_info:
        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']
        return redirect('/playlists')
    else:
        return "Error: Could not retrieve access token", 400

@app.route('/playlists')
def get_playlists():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = get(API_BASE_URL + 'me/playlists', headers=headers)
    playlists = response.json()

    return jsonify(playlists)

@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        token_data = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': client_id,
            'client_secret': client_secret
        }

        response = post(TOKEN_URL, data=token_data)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/playlists')


if __name__ == "__main__" :
    app.run(host='0.0.0.0', debug=True, port=8888)

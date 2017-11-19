from flask import Flask, redirect, jsonify, request
from flask_login import LoginManager, login_user, logout_user,\
    current_user, login_required
from oauth import OAuthSignIn
from flask_cors import CORS
from model import User, Listing
from peewee import create_model_tables
from settings import WEB_URL
import json

app = Flask(__name__)

CORS(app, supports_credentials=True)

data_source = [
    {'source': 'google', 'name': 'ABC Dental', 'address': '2101 California St',
        'phone': '1111111111', 'rating': 3, 'listed': True,	'status': True},
    {'source': 'yelp', 'name': 'ABC Dental', 'address': '2101 California St',
        'phone': '1111111111', 'rating': 3, 'listed': True,	'status': True},
    {'source': 'yahoo', 'name': 'ABC Dental', 'address': '2101 California St',
        'phone': '1111111111', 'rating': 3, 'listed': True,	'status': True},
    {'source': 'foursquare', 'name': 'ABC Dental', 'address': '2101 California St',
        'phone': '1111111111', 'rating': 3, 'listed': True,	'status': True},
    {'source': 'facebook', 'name': 'ABC Dental', 'address': '2101 California St',
        'phone': '1111111111', 'rating': 3, 'listed': True,	'status': True}
]

app.config['SECRET_KEY'] = 'top secret!'
app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': '2117634981801814',
        'secret': '1f38cd50e4671b2c82d0c827912d2cad'
    }
}

create_model_tables([User, Listing], fail_silently=True)

login_manager = LoginManager(app)
login_manager.login_view = 'index'
login_manager.login_message = 'You need to login'


@login_manager.user_loader
def load_user(id):
    return User.select().where(User.id == id).first()


@app.route('/')
def index():
    return redirect(WEB_URL)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(WEB_URL)


@app.route('/me')
@login_required
def me():
    if current_user.is_authenticated:
        user = User.select().where(User.email == current_user.email).first()
        listings = Listing.select().where(Listing.user == user)
        return (jsonify(listings=[listing.to_dict([Listing.user, Listing.id]) for listing in listings], user=user.to_dict())), 200
    return jsonify({'user_authentication': False}), 400


@app.route('/listing/<source>', methods=['POST'])
@login_required
def listings(source):
    if request.method == 'POST':
        listing = json.loads(request.data)
        try:
            print(listing)
            user = User.select().where(User.email == current_user.email).first()
            Listing.update(**listing).where(Listing.source == source, Listing.user == user).execute()
            return jsonify({'success': True}), 200
        except:
            return jsonify({'success': False})


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(WEB_URL)
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(WEB_URL)
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        return redirect(WEB_URL)
    user = User.select().where(User.social_id == social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email)
        user.save()
        for data in data_source:
            data['user'] = user
            Listing.create(**data)
    login_user(user, True)
    return redirect(WEB_URL)


if __name__ == '__main__':
    app.run(debug=True)

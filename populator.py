import requests
from bs4 import BeautifulSoup

def scrape_spotify_links():
    with open("spotifycharts.html", 'r') as chartsScrape:
        soup = BeautifulSoup(chartsScrape, 'html.parser')
    spotify_links = []

    albums = soup.find_all("tr")
    # print(len(albums))
    for album in albums:
        spotify_link = album.find("a")
        if spotify_link:
            spotify_links.append(spotify_link["href"])

    return spotify_links

# Example usage
albums = scrape_spotify_links()
from flask import Flask, request, render_template, url_for, redirect, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_mobility import Mobility
from creator import handleURL, defaultParams, getTopColorsAlone
from werkzeug.security import generate_password_hash, check_password_hash
import os, re
from progress.bar import Bar
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

os.environ['SPOTIPY_CLIENT_ID'] = '56c47550643e42b9a6ab2aa821fe394c'
os.environ['SPOTIPY_CLIENT_SECRET'] = '0f26f4b32912427ca59b7c62d8c36b5a'

db = SQLAlchemy()

class Album(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    r1 = db.Column(db.Integer)
    r2 = db.Column(db.Integer)
    r3 = db.Column(db.Integer)
    r4 = db.Column(db.Integer)
    r5 = db.Column(db.Integer)
    g1 = db.Column(db.Integer)
    g2 = db.Column(db.Integer)
    g3 = db.Column(db.Integer)
    g4 = db.Column(db.Integer)
    g5 = db.Column(db.Integer)
    b1 = db.Column(db.Integer)
    b2 = db.Column(db.Integer)
    b3 = db.Column(db.Integer)
    b4 = db.Column(db.Integer)
    b5 = db.Column(db.Integer)

def create_app():
    app = Flask(__name__)
    CORS(app)
    Mobility(app)

    app.config['SECRET_KEY'] = 'esbennielsen784'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    db.init_app(app)

    # login_manager = LoginManager()
    # login_manager.login_view = 'login'
    # login_manager.init_app(app)


    # @login_manager.user_loader
    # def load_user(user_id):
    #     # since the user_id is just the primary key of our user table, use it in the query for the user
    #     return User.query.get(int(user_id))

    # # blueprint for auth routes in our app
    # from auth import auth as auth_blueprint
    # app.register_blueprint(auth_blueprint)

    # # blueprint for non-auth parts of app
    # from server import server as server_blueprint
    # app.register_blueprint(server_blueprint)

    with app.app_context():
        db.create_all()

    return app

app = create_app()

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

class ProgressBar(Bar):
    message = "Collecting kmeans clusters ... "
    fill = "#"
    suffix = "%(index)d/%(max)d --> %(current_album)s"
    def setAlbum(self, name:str):
        self.currentAlbum = name
    @property
    def current_album(self):
        return self.currentAlbum
    
class SlowBar(Bar):
    suffix = '%(remaining_hours)d hours remaining'
    @property
    def remaining_hours(self):
        return self.eta // 3600

@app.route("/index")
def index():

    bar = ProgressBar(max = len(albums))
    for url in albums:
        url += "?"
        albumID = re.findall('album/(.*)\?', url)[0]
        # print(albumID)
        try:
            results = spotify.album(albumID)
            bar.setAlbum(results['name'])
            a = Album.query.filter_by(id = albumID).first()
            if not a:
                colors = getTopColorsAlone(url)
                # print("Colors received in app.py: ", colors)
                for i in range(len(colors), 5):
                    colors.insert(i, [255,255,255])

                # print("New Album detected: ", colors)
                newAlbum = Album(id = re.findall('album/(.*)\?', url)[0], r1 = colors[0][0], 
                    r2=colors[1][0], r3=colors[2][0], r4=colors[3][0], r5=colors[4][0],
                    g1=colors[0][1], g2=colors[1][1], g3=colors[2][1], g4=colors[3][1], g5=colors[4][1],
                    b1=colors[0][2], b2=colors[1][2], b3=colors[2][2], b4=colors[3][2], b5=colors[4][2])
                db.session.add(newAlbum)
                db.session.commit()
        except:
            print(f"Skipped {results['name']}")
        bar.next()

app.run()
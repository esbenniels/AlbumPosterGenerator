from creator import handleURL, defaultParams
import json
from flask import Flask, request, render_template, url_for, redirect, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_mobility import Mobility


db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    albumStorageLocation = db.Column(db.String(100), unique=True)

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

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)


    @login_manager.user_loader
    def load_user(user_id):
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()

    return app

app = create_app()

@app.route("/")
def home():
    id = input("enter user id: ")
    with open(f"static\\PosterStorage\\user{int(id)}\\data.json", 'r') as handle:
        data = json.load(handle)
        for item in data:
            a = db.session.get(Album, item)
            
            if data[item]['type'] == "album":
                if a:
                    colors = [[a.r1, a.g1, a.b1],[a.r2, a.g2, a.b2],[a.r3, a.g3, a.b3],[a.r4, a.g4, a.b4],[a.r5, a.g5, a.b5]]
                    handleURL(f"album/{item}?", defaultParams, "/user"+str(id), colors)
                else:
                    colors = handleURL(f"album/{item}?", defaultParams, "/user"+str(id))
                    # print("Colors received in app.py: ", colors)
                    for i in range(len(colors), 5):
                        colors.insert(i, [255,255,255])

                    # print("New Album detected: ", colors)
                    newAlbum = Album(id = item, r1 = colors[0][0], 
                        r2=colors[1][0], r3=colors[2][0], r4=colors[3][0], r5=colors[4][0],
                        g1=colors[0][1], g2=colors[1][1], g3=colors[2][1], g4=colors[3][1], g5=colors[4][1],
                        b1=colors[0][2], b2=colors[1][2], b3=colors[2][2], b4=colors[3][2], b5=colors[4][2])
                    db.session.add(newAlbum)
                    db.session.commit()
            else:
                if a:
                    colors = [[a.r1, a.g1, a.b1],[a.r2, a.g2, a.b2],[a.r3, a.g3, a.b3],[a.r4, a.g4, a.b4],[a.r5, a.g5, a.b5]]
                    handleURL(f"playlist/{item}?", defaultParams, "/user"+str(id), colors)
                else:
                    colors = handleURL(f"playlist/{item}?", defaultParams, "/user"+str(id))
                    # print("Colors received in app.py: ", colors)
                    for i in range(len(colors), 5):
                        colors.insert(i, [255,255,255])

                    # print("New Album detected: ", colors)
                    newAlbum = Album(id = item, r1 = colors[0][0], 
                        r2=colors[1][0], r3=colors[2][0], r4=colors[3][0], r5=colors[4][0],
                        g1=colors[0][1], g2=colors[1][1], g3=colors[2][1], g4=colors[3][1], g5=colors[4][1],
                        b1=colors[0][2], b2=colors[1][2], b3=colors[2][2], b4=colors[3][2], b5=colors[4][2])
                    db.session.add(newAlbum)
                    db.session.commit()
                # handleURL(f"playlist/{item}?", defaultParams, "/user"+str(id))
        handle.close()

app.run()


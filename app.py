from flask import Flask, request, render_template, url_for, redirect, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_mobility import Mobility
from creator import handleURL, defaultParams
from werkzeug.security import generate_password_hash, check_password_hash
import os, re

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
        return User.query.get(int(user_id))

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



@app.route("/index", methods=['POST', 'GET'])
@login_required
def index():
    return render_template("index.html", current_user = current_user, defaultParams=defaultParams)

@app.route("/urlSubmit", methods=['POST', 'GET'])
@login_required
def urlSubmit():
    if request.method == 'GET':
        return redirect(url_for('index'))
    else:
        url = request.form.get('SpotifyUrl')
        fields = ["coverDim", "codeDim", "cornerTextSize", "artistSize", 
                  "titleSize", "trackSize", "maxLabelLength", "maxArtistsLength", 
                  "maxTitleLength", "maxTrackLineWidth", "trackLineSpace"]
        newParams = {}
        for field in fields:
            if not request.form.get(field, None) or request.form.get(field, None) == defaultParams[field]:
                newParams[field] = int(defaultParams[field])
            else:
                newParams[field] = int(request.form.get(field))

        print("Passing Parameters: ", newParams)

        a = Album.query.filter_by(id = re.findall('album/(.*)\?', url)[0]).first()
        if a:
            colors = [[a.r1, a.g1, a.b1],[a.r2, a.g2, a.b2],[a.r3, a.g3, a.b3],[a.r4, a.g4, a.b4],[a.r5, a.g5, a.b5]]
            handleURL(url, newParams, "/user"+str(current_user.id), colors)
        else:
            colors = handleURL(url, newParams, "/user"+str(current_user.id))
            print("Colors received in app.py: ", colors)
            for i in range(len(colors), 5):
                colors.insert(i, [255,255,255])

            print("New Album detected: ", colors)
            newAlbum = Album(id = re.findall('album/(.*)\?', url)[0], r1 = colors[0][0], 
                r2=colors[1][0], r3=colors[2][0], r4=colors[3][0], r5=colors[4][0],
                g1=colors[0][1], g2=colors[1][1], g3=colors[2][1], g4=colors[3][1], g5=colors[4][1],
                b1=colors[0][2], b2=colors[1][2], b3=colors[2][2], b4=colors[3][2], b5=colors[4][2])
            db.session.add(newAlbum)
            db.session.commit()

        flash("Album poster successfully generated")
        return render_template("index.html", current_user = current_user, 
                               posterPath = "PosterStorage/user"+str(current_user.id)+"/poster.png",
                               defaultParams = defaultParams,
                               lastAlbum = url)

@app.route('/login')
def login():
    return render_template("login.html", current_user = current_user)

@app.route("/loginPost", methods = ['POST'])
def loginPost():
    # login code goes here
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('login')) # if the user doesn't exist or password is wrong, reload the page

    login_user(user, remember=remember)

    # if the above check passes, then we know the user has the right credentials
    return redirect(url_for('index'))

@app.route('/signup')
def signup():
    return render_template("signup.html", current_user = current_user)

@app.route("/signupPost", methods = ['POST'])
def signupPost():
    # code to validate and add user to database goes here

    email = request.form.get('email')
    # name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again
        flash("Email address already exists")
        return redirect(url_for('signup'))

    engine = db.get_engine().connect()
    result = engine.exec_driver_sql("""SELECT id FROM user;""")
    ids = []
    for row in result:
        print(row)
        ids.append(row[0])
    print(ids)
    ids = list(int(id) for id in ids)
    if len(ids) == 0:
        max_id = 0
    else:
        max_id = max(ids)

    try:
        os.makedirs(os.path.join(os.getcwd(), "static\\PosterStorage\\user"+str(max_id+1)))
    except:
        pass

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(email=email, albumStorageLocation = "static\\PosterStorage\\user"+str(max_id+1), password=generate_password_hash(password, method='scrypt'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    user = User.query.filter_by(email=email).first()
    login_user(user)
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


app.run(debug=True, host = '0.0.0.0')
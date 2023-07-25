from flask import Flask, request, render_template, url_for, redirect, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_mobility import Mobility
from creator import handleURL, defaultParams
from werkzeug.security import generate_password_hash, check_password_hash
import os, re, json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

os.environ['SPOTIPY_CLIENT_ID'] = '56c47550643e42b9a6ab2aa821fe394c'
os.environ['SPOTIPY_CLIENT_SECRET'] = '0f26f4b32912427ca59b7c62d8c36b5a'

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

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

        try:
            albumID = re.findall('album/(.*)\?', url)[0]
        except:
            try:
                albumID = re.findall('playlist/(.*)\?', url)[0]
            except:
                print("regex fail")
                flash("REDInvalid Spotify album URL. Try copying the link from Spotify's share options")
                return render_template("index.html", current_user=current_user, defaultParams = defaultParams)

        if len(albumID) != 22:
            print("idLength fail")
            flash("REDInvalid Spotify album URL. Try copying the link from Spotify's share options.")
            return render_template("index.html", current_user=current_user, defaultParams = defaultParams)

        try:
            results = spotify.album(albumID)
        except:
            try:
                results = spotify.playlist(albumID)
            except:
                flash("REDError retrieving Spotify Album. Check URL")
                return render_template("index.html", current_user=current_user, defaultParams = defaultParams)
        
        newParams = {}
        for field in defaultParams:
            if field == "includeFullTitle":
                # checkbox field found
                if request.form.get(field, None):
                    newParams[field] = 1
                else:
                    newParams[field] = 0
                continue
            if not request.form.get(field, None) or request.form.get(field, None) == defaultParams[field]:
                newParams[field] = int(defaultParams[field])
            else:
                newParams[field] = int(request.form.get(field))

        # print("Passing Parameters: ", newParams)

        a = Album.query.filter_by(id = albumID).first()
        if a:
            colors = [[a.r1, a.g1, a.b1],[a.r2, a.g2, a.b2],[a.r3, a.g3, a.b3],[a.r4, a.g4, a.b4],[a.r5, a.g5, a.b5]]
            handleURL(url, newParams, "/user"+str(current_user.id), colors)
        else:
            colors = handleURL(url, newParams, "/user"+str(current_user.id))
            # print("Colors received in app.py: ", colors)
            for i in range(len(colors), 5):
                colors.insert(i, [255,255,255])

            # print("New Album detected: ", colors)
            newAlbum = Album(id = albumID, r1 = colors[0][0], 
                r2=colors[1][0], r3=colors[2][0], r4=colors[3][0], r5=colors[4][0],
                g1=colors[0][1], g2=colors[1][1], g3=colors[2][1], g4=colors[3][1], g5=colors[4][1],
                b1=colors[0][2], b2=colors[1][2], b3=colors[2][2], b4=colors[3][2], b5=colors[4][2])
            db.session.add(newAlbum)
            db.session.commit()

        flash("GREENAlbum poster successfully generated")
        return render_template("index.html", current_user = current_user, 
                               posterPath = "PosterStorage/user"+str(current_user.id)+f"/poster.png",
                               defaultParams = newParams,
                               lastAlbum = url)

@app.route("/posterHistory", methods=['POST', 'GET'])
@login_required
def posterHistory():

    posterNames = os.listdir(f"static\\PosterStorage\\user{str(current_user.id)}")
    posterNames = [file for file in posterNames if file.__contains__('.png') and not file.__contains__("poster")]

    paramDict = {}
    with open(f"static/PosterStorage/user{str(current_user.id)}/data.json", 'r+') as handle:
        data = json.load(handle)
        for poster in posterNames:
            if not poster.__contains__("poster"):
                paramDict[poster] = data[poster.replace('.png','')]
        handle.close()

    numRows = (len(posterNames)//4)+1 if len(posterNames) > 0 else 0

    # print("Posters: ", posterNames)
    # print("Number of posters to show: ", len(posterNames))
    # print("Number of rows: ", numRows)
    numColumns : list[int] = []
    tracker = len(posterNames)
    for i in range(numRows):
        if i == numRows - 1:
            numColumns.append(tracker)
            tracker = 0
        else:
            numColumns.append(4)
            tracker -= 4
    # print("Number of columns: ", numColumns)
    albumPlaylistNames: list[str] = []
    artistNames: list[str] = []

    for albumID in posterNames:
        try:
            albumPlaylistNames.append(spotify.album(albumID.replace(".png",""))['name'])
        except:
            albumPlaylistNames.append(spotify.playlist(albumID.replace(".png",""))['name'])
        
        try:
            results = spotify.album(albumID.replace(".png",""))
            build : str = ''
            for i in range(len(results['artists'])):
                # print(results['artists'][i]['name'], end="")
                build += results['artists'][i]['name']
                if not i == len(results['artists'])-1:
                    build += ", "
            artistNames.append(build)
        except:
            artistNames.append(spotify.playlist(albumID.replace(".png",""))['owner']['display_name'])
    # print(albumNames)

    bigStruct: list[dict] = [
        {
            "file": posterNames[i],
            "name": albumPlaylistNames[i],
            "params": paramDict[posterNames[i]],
            "artist": artistNames[i]
        }
        for i in range(len(posterNames))
    ]

    return render_template("posters.html",
                        #    posterNames = posterNames,
                        allData = bigStruct,
                        numPosters = len(posterNames),
                        #    paramDict = paramDict,
                        numRows = numRows,
                        numColumns = numColumns,
                        current_user = current_user,
                        #    albumNames = albumPlaylistNames
                    )

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
        flash('REDPlease check your login details and try again.')
        return render_template('login.html') # if the user doesn't exist or password is wrong, reload the page

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
        flash("REDEmail address already exists")
        return render_template("signup.html")

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

    with open(os.path.join(os.getcwd(), "static\\PosterStorage\\user"+str(max_id+1))+"\\data.json", 'w+') as newFileHandle:
        json.dump({"id": max_id+1}, newFileHandle)
        newFileHandle.close()

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


app.run(host = '0.0.0.0')


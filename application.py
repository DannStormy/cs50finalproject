from flask import Flask, flash, redirect, render_template, request, session, url_for, send_file
from flask_session import Session
import sqlite3
from sqlite3 import connect
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import cgi, os.path
import cgitb; cgitb.enable()
from functools import wraps
from tempfile import mkdtemp
import datetime
from io import BytesIO
import os





ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config.update(
    TESTING=True,
    SECRET_KEY=b'_5#y2L"F4Q8z\n\xec]/'
)


if __name__ == "__main__":
    app.run(host='0.0.0.0')


times = int(os.environ.get('TESTING', None))




Session(app)
filePath = os.path.abspath("database.db")
conn = connect(filePath, check_same_thread=False)
db = conn.cursor()



@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function





@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "GET":
        return render_template("index.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        if not username:
            return "please input username"
        if not password:
            return "please input password"
        rows = db.execute("SELECT * FROM users WHERE username = :username", ([username]))
        conn.commit()
        for row in rows:
            hash_password = row[2]
            current_id = row[0]
            if row[1] == username and check_password_hash(hash_password, password):

                #remembe which user logged in
                session['user_id'] = current_id
                flash("Logged In")
                return redirect("/makealist")
        flash("error 404")
        return "error, invalid name/password"

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Logged Out")
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        if not username:
            return "must enter username"
        password = request.form.get("password")
        if not password:
            return "must enter password"
        confirmation = request.form.get("confirmation")
        if password != confirmation:
            return "passwords don't match"
        hash_password = generate_password_hash(password)
        existing_username = db.execute("SELECT * FROM users WHERE username = :username", ([username]))
        if existing_username.fetchone() is not None:
            flash("username exists already")
            return render_template("register.html")
        else:
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", (username,hash_password))
            conn.commit()
            conn.close
            print("Successfully Registered")
            flash("Registered")
            return render_template("index.html")
    

@app.route("/makealist", methods=["GET", "POST"])
@login_required
def makewish():
    if request.method == "GET":
        return render_template("bucketlist.html")  
    else:
        user_id = session["user_id"]
        if user_id:
            wish = request.form.get("wish")
            if wish == '':
                flash("please insert wish")
                return redirect("/makealist")
            else:
                now = datetime.datetime.now()
                x = now.strftime("%m/%d/%Y, %H:%M:%S")
                db.execute("INSERT INTO bucketlist (wish_id,wish, added) VALUES (:wish_id, :wish, :added)", [user_id, wish, x])
                conn.commit()
                flash("wish added")
                return redirect("/makealist")

@app.route("/mybucketlist")
@login_required
def mylist():
    history = db.execute("SELECT * FROM bucketlist WHERE wish_id = :wish_id", (session["user_id"],))
    conn.commit()
    listoutput=[i for i in history]
    return render_template("list.html", lists = listoutput)

@app.route("/mybucketlist", methods=["GET", "POST"])
@login_required
def delete():
    if request.method == "POST":
        value = request.form.get("list-value")
        db.execute("DELETE FROM bucketlist WHERE wish_id = :wish_id AND wish = :wish", (session["user_id"], value))
        conn.commit()
        flash("wish deleted")
        return redirect("/mybucketlist")




def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData






@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        city = request.form.get("city")
        country = request.form.get("country")
        interest = request.form.get("interest")
        bio = request.form.get("bio")
        uploaded_file = request.files['file'].filename
        f = request.files['file']
        f.save(secure_filename(f.filename))
        empPicture = convertToBinaryData(uploaded_file)
        user = session["user_id"]        
        check_row = db.execute("SELECT COUNT(*) FROM profiles WHERE profile_id = :profile_id", (user,))
        for i in check_row:
            countofrows = i[0]        
        if countofrows == 0:
            db.execute("INSERT INTO profiles (profile_id, city, country, interest, bio, picture) VALUES (:user, :city, :country, :interest, :bio, :picture)",
            [user, city, country, interest, bio, sqlite3.Binary(empPicture)])
            conn.commit()
            flash("profile completed")
            return redirect("/profile")
        elif countofrows == 1:                
            db.execute("UPDATE profiles SET city = :city, country = :country, interest = :interest, bio = :bio, picture = :picture WHERE profile_id = :profile_id",
            [city, country, interest, bio, sqlite3.Binary(empPicture), session["user_id"]])
            conn.commit()
            flash("profile updated")
            return redirect("/profile")
    else:
        displayrows = db.execute("SELECT * FROM profiles WHERE profile_id = :profile_id", (session["user_id"],))
        displayrows = db.fetchall()
        displaycount = db.execute("SELECT COUNT(*) FROM bucketlist WHERE wish_id = :wish_id", (session["user_id"],))
        for i in displaycount:
            bucketsize = i[0]
        #get username
        check_user = db.execute("SELECT username FROM users WHERE id = :user_id", (session["user_id"],))
        for i in check_user:
           user = i[0]
        return render_template("profile.html", rows = displayrows, user = user, count = bucketsize)

@app.route('/i/<int:ident>')
def profile_image(ident):
    displayrows = db.execute("SELECT * FROM profiles WHERE profile_id = :profile_id", (ident,))
    displayrows = db.fetchall()
    for i in displayrows:
        image_bytes = i[5]
    bytes_io = BytesIO(image_bytes)

    return send_file(bytes_io, mimetype='image/jpeg')


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "POST":
        displayvalues = db.execute("SELECT * FROM profiles WHERE profile_id = :profile_id", (session["user_id"],))
        displayvalues = db.fetchall()
        return render_template("edit.html", row = displayvalues)
    else:
        return render_template("edit.html")
        



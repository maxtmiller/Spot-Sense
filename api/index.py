import requests
import base64
import os
from io import BytesIO
import io
from PIL import Image

from dotenv import load_dotenv
load_dotenv()

import sqlite3
from flask import Flask, flash, redirect, render_template, session, request, jsonify, send_file
from flask_session import Session

from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, before_first_request, check_for_sql, clear_session, generate_password, valid_email, classification_model, cohere_chat

from google.oauth2 import id_token
from google.auth.transport import requests


app = Flask(__name__, template_folder='../templates', static_folder="../static")


app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def get_db_connection():
    """Create and return a new database connection."""
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    return conn


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.before_request
@before_first_request
def before_request():
    """Clear Session"""

    # Checks if college list is populated
    check_for_sql(app)

    # Calls function to redirect to login page only on app start
    clear_session(app)

    return


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Clear any user_id
    session.clear()

    conn = get_db_connection()
    db = conn.cursor()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Variable for storing error message
        error = None

        # Ensure username was submitted
        if not request.form.get("user"):
            error = "Must provide email or username!"
            conn.close()
            return render_template("login.html", error=error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "Must provide password!"
            conn.close()
            return render_template("login.html", error=error)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ? OR email = ?", (request.form.get("user"), request.form.get("user"))).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            error = "Invalid username and/or password!"
            conn.close()
            return render_template("login.html", error=error)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        print("success")
        conn.close()
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        conn.close()
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    conn = get_db_connection()
    db = conn.cursor()

    if request.method == "POST":

        new_email = request.form.get("email")
        new_username = request.form.get("username")
        new_password = request.form.get("password")
        new_confirmation = request.form.get("confirmation")

        existing_email = db.execute("SELECT * FROM users WHERE email = ?", (new_email,)).fetchall()
        existing_username = db.execute("SELECT * FROM users WHERE username = ?", (new_username,)).fetchall()

        # Variable for storing error message
        error = None

        # Ensure email was submitted
        if not new_email:
            error = "Must provide email!"
            conn.close()
            return render_template("register.html", error=error)
        
        # Ensure email is not already registered to an account
        elif len(existing_email) != 0:
            error = "Account already exists with specified email!"
            conn.close()
            return render_template("register.html", error=error)
        
        # Ensure follows the correct format
        elif valid_email(new_email) == False:
            error = "Invalid email provided!"
            conn.close()
            return render_template("register.html", error=error)

        # Ensure username is provided
        elif not new_username:
            error = "Must provide username!"
            conn.close()
            return render_template("register.html", error=error)

        # Ensure username is unique
        elif len(existing_username) != 0:
            error = "Username not available!"
            conn.close()
            return render_template("register.html", error=error)

        # Ensure password was submitted
        elif not new_password:
            error = "Missing password!"
            conn.close()
            return render_template("register.html", error=error)

        # Ensure passwords match
        elif new_password != new_confirmation:
            error = "Passwords don't match!"
            conn.close()
            return render_template("register.html", error=error)

        # Ensure password is between 4 and 15 characters
        elif len(new_password) < 4 or len(new_password) > 15:
            error = "Password must be between 4 and 15 characters long!"
            conn.close()
            return render_template("register.html", error=error)

        # Hashes password when before inserting into users table
        hash = generate_password_hash(new_password, method='pbkdf2', salt_length=16)

        db.execute("INSERT INTO USERS (email, username, hash, auto_generated) VALUES(?, ?, ?, ?)", (new_email, new_username, hash, False))
        conn.commit()

        rows = db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),)).fetchall()

        session["user_id"] = rows[0]["id"]

        flash("Registered!")
        conn.close()
        return redirect("/")

    else:
        conn.close()
        return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/")
@login_required
def home():
    """Main Page"""

    conn = get_db_connection()
    db = conn.cursor()

    user_id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()

    conn.close()
    return render_template("home.html", user=user)


@app.route("/classify", methods=["POST"])
@login_required
def classify():
    """Classify Skin Cancer from Model"""

    conn = get_db_connection()
    db = conn.cursor()

    user_id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()

    data = request.get_json()
    image_data = data.get("image")

    image_data = image_data.split(',')[1]
    image_bytes = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_bytes))

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    vals = classification_model(img_byte_arr)

    print(vals[1],type(vals[1]))
    db.execute("INSERT INTO images (image, user_id, classification, accuracy) VALUES (?, ?, ?, ?)", (sqlite3.Binary(image_bytes),user_id,vals[0],str(vals[1])))
    conn.commit()

    conn.close()

    if (vals[0]=="malignant"):
        flash("Skin likely Malignant!")
        return redirect("/help")

    flash("Skin likely Benign!")
    return redirect("/images")


@app.route("/help")
@login_required
def help():
    """Help Page"""

    conn = get_db_connection()
    db = conn.cursor()

    user_id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()

    conn.close()
    return render_template("help.html", user=user)


@app.route("/map")
@login_required
def map():
    """Logic for finding nearby hospitals"""

    conn = get_db_connection()
    db = conn.cursor()

    user_id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()

    conn.close()
    return render_template("map.html", user=user)


@app.route("/chatbot")
@login_required
def chatbot():
    """Logic for chatbot page"""

    conn = get_db_connection()
    db = conn.cursor()

    user_id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()

    conn.close()
    return render_template("chatbot.html", user=user)


@app.route("/chatbot/message", methods=["POST"])
@login_required
def chatbot_message():

    user_message = request.json["message"]

    bot_response = cohere_chat(user_message)

    return jsonify({"response": bot_response})


def get_image_from_db(image_id):
    """Retrieve Image from Database"""

    conn = get_db_connection()
    db = conn.cursor()
    
    image_data = db.execute("SELECT image FROM images WHERE id = ?", (image_id,)).fetchone()
    
    if image_data:
        conn.close()
        return image_data[0]
    conn.close()
    return None


@app.route('/view_image/<int:image_id>')
@login_required
def view_image(image_id):
    """Fetch image data from the database"""

    conn = get_db_connection()
    db = conn.cursor()

    user_id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()

    image_ids = db.execute("SELECT id FROM images WHERE user_id = ?", (user_id,)).fetchall()
    image_ids = [image[0] for image in image_ids]

    if image_id not in image_ids:
        images_data = db.execute("SELECT id, classification, accuracy FROM images WHERE user_id = ?", (user_id,)).fetchall()
        conn.close()
        flash("Unauthorized Access!")
        return render_template("images.html", images=images_data, user=user)

    image_data = get_image_from_db(image_id)

    if image_data:
        conn.close()
        return send_file(io.BytesIO(image_data), mimetype='image/png')
    conn.close()
    return "Image not found", 404


@app.route("/images")
@login_required
def images():
    """Display Images"""

    conn = get_db_connection()
    db = conn.cursor()

    user_id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()
    
    # Fetch Image IDs
    images_data = db.execute("SELECT id, classification, accuracy FROM images WHERE user_id = ?", (user_id,)).fetchall()
    print(images)
    
    conn.close()

    return render_template("images.html", images=images_data, user=user)


@app.route("/settings", methods=["GET", "POST"] )
@login_required
def settings():
    """Settings Page"""

    conn = get_db_connection()
    db = conn.cursor()

    user_id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()

    generated = user['auto_generated']

    if request.method == "POST":

        error = None
        success = None

        new_username = request.form.get("username")
        new_email = request.form.get("email")
        display = request.form.get("display")
       
        if generated:
            set_password = request.form.get("set-password")
        else:
            new_password = request.form.get("new-password")
            current_password = request.form.get("current-password")

        existing_usernames = db.execute("SELECT * FROM users WHERE username = ? AND NOT id = ?", (new_username, user['id']))
        existing_emails = db.execute("SELECT * FROM users WHERE email = ? AND NOT id = ?", (new_email, user['id']))

        hash = db.execute("SELECT hash FROM users WHERE id = ?", user['id'])[0]['hash']

        if not new_username or not new_email:
            error = "Must fill all fields!"
            conn.close()
            return render_template("settings.html",  user=user, error=error)
        
        elif len(existing_usernames) != 0:
            error = "Username already taken!"
            conn.close()
            return render_template("settings.html",  user=user, error=error)

        elif len(existing_emails) != 0:
            error = "Account already exists for specified email!"
            conn.close()
            return render_template("settings.html",  user=user, error=error)

        elif valid_email(new_email) == False:
            error = "Invalid email provided!"
            conn.close()
            return render_template("settings.html",  user=user, error=error)

        elif generated:

            if len(set_password) < 4 or len(set_password) > 15:
                error = "Password must be between 4 and 15 characters long!"
                conn.close()
                return render_template("settings.html",  user=user, error=error)

        elif not generated:

            if not current_password:
                error = "Current password not provided!"
                conn.close()
                return render_template("settings.html",  user=user, error=error)
            
            elif not check_password_hash(hash, current_password):
                error = "Current password incorrect!"
                conn.close()
                return render_template("settings.html",  user=user, error=error)

            elif display == "flex":

                if new_username == user['username'] and new_email == user['email'] and check_password_hash(hash, current_password) and (not new_password or new_password == current_password):
                    error = "Account Details have not changed!"
                    print("all")
                    conn.close()
                    return render_template("settings.html",  user=user, error=error)
                
                elif not new_password:
                    error = "New password not set!"
                    conn.close()
                    return render_template("settings.html",  user=user, error=error)
                
                elif len(new_password) < 4 or len(new_password) > 15:
                    error = "New password must be between 4 and 15 characters long!"
                    conn.close()
                    return render_template("settings.html",  user=user, error=error)

        if generated:

            if new_username == user['username'] and new_email != user['email']:
                db.execute("UPDATE users SET email = ? WHERE id = ?;", new_email, user['id'])
                success = "Email succesfully updated!"
                conn.close()
                return render_template("settings.html",  user=user, success=success)
            
            elif new_username != user['username'] and new_email == user['email']:
                db.execute("UPDATE users SET username = ? WHERE id = ?;", new_username, user['id'])
                success = "Username succesfully updated!"
                conn.close()
                return render_template("settings.html",  user=user, success=success)
            
            else:
                hash = generate_password_hash(set_password, method='pbkdf2', salt_length=16)
                db.execute("UPDATE users SET hash = ?;", hash)
                db.execute("UPDATE users SET auto_generated = ?;", False)
                success = "Password succesfully set!"
                conn.close()
                return render_template("settings.html",  user=user, success=success)

        elif not generated:

            if new_username == user['username'] and new_email != user['email'] and check_password_hash(hash, current_password) and display == "none":
                db.execute("UPDATE users SET email = ? WHERE id = ?;", new_email, user['id'])
                success = "Email succesfully updated!"
                conn.close()
                return render_template("settings.html",  user=user, success=success)
            
            elif new_username != user['username'] and new_email == user['email'] and check_password_hash(hash, current_password) and display == "none":
                db.execute("UPDATE users SET username = ? WHERE id = ?;", new_username, user['id'])
                success = "Username succesfully updated!"
                conn.close()
                return render_template("settings.html",  user=user, success=success)
            
            elif new_username != user['username'] and new_email != user['email'] and check_password_hash(hash, current_password) and display == "none":
                db.execute("UPDATE users SET username = ?, email = ? WHERE id = ?;", new_username, new_email, user['id'])
                success = "Email & Username succesfully updated!"
                conn.close()
                return render_template("settings.html",  user=user, success=success)
            
            elif new_username == user['username'] and new_email == user['email'] and new_password != current_password and check_password_hash(hash, current_password) and new_password and display == "flex":
                hash = generate_password_hash(new_password, method='pbkdf2', salt_length=16)
                db.execute("UPDATE users SET hash = ?;", hash)
                success = "Password succesfully updated!"
                conn.close()
                return render_template("settings.html",  user=user, success=success)
            
            else:
                error = "Password must be updated alone!"
                conn.close()
                return render_template("settings.html",  user=user, error=error)

        conn.close()
        return render_template("settings.html",  user=user)

    conn.close()
    return render_template("settings.html",  user=user, generated=generated)


@app.route("/about")
@login_required
def about():
    """About Page"""

    conn = get_db_connection()
    db = conn.cursor()

    user_id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()

    conn.close()
    return render_template("about.html",  user=user)


@app.route('/google-signin', methods=['POST'])
def google_signin():
    """Google Signin"""
        
    YOUR_CLIENT_ID = os.getenv('CLIENTID')

    id_token_received = request.form['id_token']

    conn = get_db_connection()
    db = conn.cursor()

    try:

        idinfo = id_token.verify_oauth2_token(id_token_received, requests.Request(), YOUR_CLIENT_ID)

        user_id = idinfo['sub']
        user_name = idinfo['name']
        user_email = idinfo['email']

        email_count = db.execute("SELECT COUNT(email) FROM users WHERE email = ?;", (user_email,)).fetchone()
        email_count = email_count[0]

        if email_count != 1:

            email = user_email
            username = user_name
            password = generate_password(12)
            hash = generate_password_hash(password, method='pbkdf2', salt_length=16)

            db.execute("INSERT INTO USERS (email, username, hash, auto_generated) VALUES(?, ?, ?, ?);", (email, username, hash, True))
            conn.commit()

            rows = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchall()

            print("rows - ", rows)

            session["user_id"] = rows[0]["id"]

        else:

            email = user_email

            rows = db.execute("SELECT * FROM users WHERE email = ?;", (email,)).fetchall()

            session["user_id"] = rows[0]["id"]

        conn.close()
        return jsonify(success=True)

    except ValueError:
        print('Invalid token')
        conn.close()
        return jsonify(success=False, error='Invalid token')


if __name__ == "__main__":
    port = int(os.getenv('PORT', 3000))
    app.run(host="0.0.0.0", port=port, debug=True)
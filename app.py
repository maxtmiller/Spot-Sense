import os.path
import requests
import json
from iso639 import Lang
from datetime import datetime

import sqlite3
from flask import Flask, flash, redirect, render_template, session, request, jsonify
from flask_session import Session

from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, before_first_request, check_for_sql, clear_session, generate_password, valid_email

from google.oauth2 import id_token
from google.auth.transport import requests


app = Flask(__name__)


app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


conn = sqlite3.connect("static/sql/database.db", check_same_thread=False)
conn.row_factory = sqlite3.Row  # To allow dictionary-like row access
db = conn.cursor()

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

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Variable for storing error message
        error = None

        # Ensure username was submitted
        if not request.form.get("user"):
            error = "Must provide email or username!"
            return render_template("login.html", error=error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "Must provide password!"
            return render_template("login.html", error=error)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ? OR email = ?", (request.form.get("user"), request.form.get("user"))).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            error = "Invalid username and/or password!"
            return render_template("login.html", error=error)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        print("success")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        new_email = request.form.get("email")
        new_username = request.form.get("username")
        new_password = request.form.get("password")
        new_confirmation = request.form.get("confirmation")

        existing_email = db.execute("SELECT * FROM users WHERE email = ?", (new_email)).fetchall()
        existing_username = db.execute("SELECT * FROM users WHERE username = ?", (new_username)).fetchall()

        # Variable for storing error message
        error = None

        # Ensure email was submitted
        if not new_email:
            error = "Must provide email!"
            return render_template("register.html", error=error)
        
        # Ensure email is not already registered to an account
        elif len(existing_email) != 0:
            error = "Account already exists with specified email!"
            return render_template("register.html", error=error)
        
        # Ensure follows the correct format
        elif valid_email(new_email) == False:
            error = "Invalid email provided!"
            return render_template("register.html", error=error)

        # Ensure username is provided
        elif not new_username:
            error = "Must provide username!"
            return render_template("register.html", error=error)

        # Ensure username is unique
        elif len(existing_username) != 0:
            error = "Username not available!"
            return render_template("register.html", error=error)

        # Ensure password was submitted
        elif not new_password:
            error = "Missing password!"
            return render_template("register.html", error=error)

        # Ensure passwords match
        elif new_password != new_confirmation:
            error = "Passwords don't match!"
            return render_template("register.html", error=error)

        # Ensure password is between 4 and 15 characters
        elif len(new_password) < 4 or len(new_password) > 15:
            error = "Password must be between 4 and 15 characters long!"
            return render_template("register.html", error=error)

        # Hashes password when before inserting into users table
        hash = generate_password_hash(new_password, method='pbkdf2', salt_length=16)

        db.execute("INSERT INTO USERS (email, username, hash, auto_generated) VALUES(?, ?, ?, ?)", new_email, new_username, hash, False)
        conn.commit()

        rows = db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"))).fetchall()

        session["user_id"] = rows[0]["id"]

        flash("Registered!")
        return redirect("/")

    else:

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

    user_id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()


    return render_template("home.html", user=user)


@app.route("/settings", methods=["GET", "POST"] )
@login_required
def settings():
    """Settings Page"""

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

        existing_usernames = db.execute("SELECT * FROM users WHERE username = ? AND NOT id = ?", new_username, user['id'])
        existing_emails = db.execute("SELECT * FROM users WHERE email = ? AND NOT id = ?", new_email, user['id'])

        hash = db.execute("SELECT hash FROM users WHERE id = ?", user['id'])[0]['hash']

        if not new_username or not new_email:
            error = "Must fill all fields!"
            return render_template("settings.html",  user=user, error=error)
        
        elif len(existing_usernames) != 0:
            error = "Username already taken!"
            return render_template("settings.html",  user=user, error=error)

        elif len(existing_emails) != 0:
            error = "Account already exists for specified email!"
            return render_template("settings.html",  user=user, error=error)

        elif valid_email(new_email) == False:
            error = "Invalid email provided!"
            return render_template("settings.html",  user=user, error=error)

        elif generated:

            if len(set_password) < 4 or len(set_password) > 15:
                error = "Password must be between 4 and 15 characters long!"
                return render_template("settings.html",  user=user, error=error)

        elif not generated:

            if not current_password:
                error = "Current password not provided!"
                return render_template("settings.html",  user=user, error=error)
            
            elif not check_password_hash(hash, current_password):
                error = "Current password incorrect!"
                return render_template("settings.html",  user=user, error=error)

            elif display == "flex":

                if new_username == user['username'] and new_email == user['email'] and check_password_hash(hash, current_password) and (not new_password or new_password == current_password):
                    error = "Account Details have not changed!"
                    print("all")
                    return render_template("settings.html",  user=user, error=error)
                
                elif not new_password:
                    error = "New password not set!"
                    return render_template("settings.html",  user=user, error=error)
                
                elif len(new_password) < 4 or len(new_password) > 15:
                    error = "New password must be between 4 and 15 characters long!"
                    return render_template("settings.html",  user=user, error=error)

        if generated:

            if new_username == user['username'] and new_email != user['email']:
                db.execute("UPDATE users SET email = ? WHERE id = ?;", new_email, user['id'])
                success = "Email succesfully updated!"
                return render_template("settings.html",  user=user, success=success)
            
            elif new_username != user['username'] and new_email == user['email']:
                db.execute("UPDATE users SET username = ? WHERE id = ?;", new_username, user['id'])
                success = "Username succesfully updated!"
                return render_template("settings.html",  user=user, success=success)
            
            else:
                hash = generate_password_hash(set_password, method='pbkdf2', salt_length=16)
                db.execute("UPDATE users SET hash = ?;", hash)
                db.execute("UPDATE users SET auto_generated = ?;", False)
                success = "Password succesfully set!"
                return render_template("settings.html",  user=user, success=success)

        elif not generated:

            if new_username == user['username'] and new_email != user['email'] and check_password_hash(hash, current_password) and display == "none":
                db.execute("UPDATE users SET email = ? WHERE id = ?;", new_email, user['id'])
                success = "Email succesfully updated!"
                return render_template("settings.html",  user=user, success=success)
            
            elif new_username != user['username'] and new_email == user['email'] and check_password_hash(hash, current_password) and display == "none":
                db.execute("UPDATE users SET username = ? WHERE id = ?;", new_username, user['id'])
                success = "Username succesfully updated!"
                return render_template("settings.html",  user=user, success=success)
            
            elif new_username != user['username'] and new_email != user['email'] and check_password_hash(hash, current_password) and display == "none":
                db.execute("UPDATE users SET username = ?, email = ? WHERE id = ?;", new_username, new_email, user['id'])
                success = "Email & Username succesfully updated!"
                return render_template("settings.html",  user=user, success=success)
            
            elif new_username == user['username'] and new_email == user['email'] and new_password != current_password and check_password_hash(hash, current_password) and new_password and display == "flex":
                hash = generate_password_hash(new_password, method='pbkdf2', salt_length=16)
                db.execute("UPDATE users SET hash = ?;", hash)
                success = "Password succesfully updated!"
                return render_template("settings.html",  user=user, success=success)
            
            else:
                error = "Password must be updated alone!"
                return render_template("settings.html",  user=user, error=error)

        return render_template("settings.html",  user=user)

    return render_template("settings.html",  user=user, generated=generated)


@app.route('/google-signin', methods=['POST'])
def google_signin():

    with open('./static/cred.json', 'r') as file:
        data = json.load(file)['clientID']
        
    YOUR_CLIENT_ID = data
    print(YOUR_CLIENT_ID)

    id_token_received = request.form['id_token']

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

        return jsonify(success=True)

    except ValueError:
        print('Invalid token')
        return jsonify(success=False, error='Invalid token')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="3000", debug=True)
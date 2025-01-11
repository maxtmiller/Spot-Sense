import os
import secrets
import string
import re
import json

from openai import OpenAI
from pydub import AudioSegment
from pydub.playback import play
from os import path
from iso639 import Lang

from cs50 import SQL
from functools import wraps
from flask import redirect, session, request, current_app

import os.path
from sqlite3 import Error


def login_required(f):
    """Decorate routes to require login"""

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if session.get("user_id") is None:

            return redirect("/login")

        return f(*args, **kwargs)

    return decorated_function


def before_first_request(f):
    """Decorate routes to execute before first request"""

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not current_app.config.get("BEFORE_FIRST_REQUEST"):

            return f(*args, **kwargs)

            current_app.config["BEFORE_FIRST_REQUEST"] = True

    return decorated_function

# Runs SQL from file
def run_sql(sql_file):
    """Runs SQL Commands from SQL File"""

    db = SQL("sqlite:///static/sql/database.db")

    try:
        with open('./static/sql/'+sql_file, 'r') as file:
            sql_commands = file.read().split(';')
        for command in sql_commands:
            if command.strip():
                db.execute(command)
    except Error as e:
        print(e)

# Creates SQL structures if they don't exist
def check_for_sql(app):
    """Runs SQL files if they have not been run before"""

    db = SQL("sqlite:///static/sql/database.db")

    if not app.config.get("BEFORE_CHECK_EXECUTED"):

        run_sql('schema.sql')

        return

        app.config["BEFORE_CHECK_EXECUTED"] = True

# Clears local flask sessions
def clear_session(app):
    """Clears Session and redirects to login page"""

    if not app.config.get("BEFORE_REQUEST_EXECUTED"):

        if request.endpoint != 'static' and request.endpoint != 'login':

            session.clear()

            return redirect("/login")

        app.config["BEFORE_REQUEST_EXECUTED"] = True

# Generates a random password
def generate_password(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password

#Checks for correct email regex
def valid_email(email):
    emailRegex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    return re.match(emailRegex, email) is not None

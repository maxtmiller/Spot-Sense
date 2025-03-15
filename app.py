import base64
import os
from io import BytesIO
import io
from PIL import Image

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, flash, redirect, render_template, request, jsonify, session
from flask_session import Session

from helpers import login_required, valid_email, classification_model, cohere_chat, upload_image

from google.oauth2 import id_token
from google.auth.transport import requests

import firebase_admin
from firebase_admin import credentials, firestore, storage, auth


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred, {
    "storageBucket": "spotsense-5af66.firebasestorage.app"
})

db = firestore.client()
bucket = storage.bucket()


@app.route("/firebase-config")
def firebase_config():
    """Serve Firebase credentials securely"""
    
    return jsonify({
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("FIREBASE_APP_ID"),
        "measurementId":  os.getenv("FIREBASE_MEASUREMENT_ID")
    })


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in using Firebase Authentication and Firestore"""
    session.clear()

    if request.method == "POST":
        id_token = request.json.get("id_token")

        if not id_token:
            return jsonify({"error": "Missing ID token"}), 400

        try:
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token["uid"]
            email = decoded_token.get("email")

            user_ref = db.collection("users").document(user_id)
            user_doc = user_ref.get()

            if not user_doc.exists:
                return jsonify({"error": "User not found in Firestore!"}), 404

            session["user_id"] = user_id
            session["email"] = email

            return jsonify({"message": "Login successful"}), 200

        except Exception as e:
            print("Firebase Auth Error:", e)
            return jsonify({"error": f"Authentication failed: {str(e)}"}), 401

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user using Firebase Authentication and store details in Firestore"""

    if request.method == "POST":

        new_email = request.form.get("email")
        new_username = request.form.get("username")
        new_password = request.form.get("password")
        new_confirmation = request.form.get("confirmation")

        error = None

        if not new_email:
            error = "Must provide email!"
        elif valid_email(new_email) == False:
            error = "Invalid email provided!"
        elif not new_username:
            error = "Must provide username!"
        elif not new_password:
            error = "Missing password!"
        elif new_password != new_confirmation:
            error = "Passwords don't match!"
        elif len(new_password) < 4 or len(new_password) > 15:
            error = "Password must be between 4 and 15 characters long!"

        if error:
            return render_template("register.html", error=error)

        try:
            user = auth.create_user(email=new_email, password=new_password)
            print(f"User created: {user.uid}")
        except firebase_admin.exceptions.FirebaseError as e:
            error = f"Failed to create user: {str(e)}"
            return render_template("register.html", error=error)

        try:
            user_ref = db.collection("users").document(user.uid)
            user_ref.set({
                "email": new_email,
                "username": new_username,
                "user_id": user.uid,
                "auto_generated": False
            })
            print(f"User {user.uid} added to Firestore")
        except Exception as e:
            error = f"Error storing user in Firestore: {str(e)}"
            return render_template("register.html", error=error)

        session["user_id"] = user.uid
        flash("Registered successfully!")
        return redirect("/")

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

    try:
        user_ref = db.collection("users").document(user_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return redirect("/login")

        user = user_doc.to_dict()

        return render_template("home.html", user=user)

    except Exception as e:
        print("Firestore Error:", e)
        return redirect("/login") 


@app.route("/classify", methods=["POST"])
@login_required
def classify():
    """Classify Skin Cancer from Model"""

    user_id = session["user_id"]

    data = request.get_json()
    image_data = data.get("image")

    image_data = image_data.split(',')[1]
    image_bytes = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_bytes))

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    vals = classification_model(img_byte_arr)

    image_path = f"images/{user_id}/{str(hash(image_data))}.png"

    image_url = upload_image(image_bytes, image_path, bucket)

    result_data = {
        "user_id": user_id,
        "classification": vals[0],
        "accuracy": str(vals[1]),
        "image_url": image_url,
    }

    db.collection("images").add(result_data)

    if (vals[0]=="malignant"):
        flash("Skin likely Malignant!")
        return redirect("/help")

    flash("Skin likely Benign!")
    return redirect("/images")


@app.route("/help")
@login_required
def help():
    """Help Page"""

    user_id = session["user_id"]
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    user = user_doc.to_dict()

    return render_template("help.html", user=user)


@app.route("/map")
@login_required
def map():
    """Logic for finding nearby hospitals"""

    user_id = session["user_id"]
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    user = user_doc.to_dict()

    return render_template("map.html", user=user)


@app.route("/chatbot")
@login_required
def chatbot():
    """Logic for chatbot page"""

    user_id = session["user_id"]
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    user = user_doc.to_dict()

    return render_template("chatbot.html", user=user)


@app.route("/chatbot/message", methods=["POST"])
@login_required
def chatbot_message():

    user_message = request.json["message"]

    bot_response = cohere_chat(user_message)

    return jsonify({"response": bot_response})


@app.route("/images")
@login_required
def images():
    """Display Images"""

    user_id = session["user_id"]
    
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    user = user_doc.to_dict()

    images_ref = db.collection("images")
    images_query = images_ref.where("user_id", "==", user_id)
    images_docs = images_query.stream()

    images_data = []
    for image_doc in images_docs:
        image_data = image_doc.to_dict()
        image_data["id"] = image_doc.id
        
        image_data["image_url"] = image_data.get("image_url")
        
        images_data.append(image_data)

    return render_template("images.html", images=images_data, user=user)


@app.route("/settings", methods=["GET", "POST"] )
@login_required
def settings():
    """Settings Page"""

    user_id = session["user_id"]
    
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    user = user_doc.to_dict()
    
    return render_template("settings.html",  user=user)


@app.route("/about")
@login_required
def about():
    """About Page"""

    user_id = session["user_id"]

    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    user = user_doc.to_dict()


    return render_template("about.html",  user=user)


if __name__ == "__main__":
    app.run()
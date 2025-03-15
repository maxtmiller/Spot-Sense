import os
import secrets
import string
import re
import cohere
import requests

from dotenv import load_dotenv
load_dotenv()

from functools import wraps
from flask import redirect, session, request, current_app

import os.path

import tensorflow as tf
from tensorflow.keras import models
import numpy as np


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


def clear_session(app):
    """Clears Session and redirects to login page"""

    if not app.config.get("BEFORE_REQUEST_EXECUTED"):

        if request.endpoint != 'static' and request.endpoint != 'login':

            session.clear()

            return redirect("/login")

        app.config["BEFORE_REQUEST_EXECUTED"] = True


def generate_password(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password


def valid_email(email):
    emailRegex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    return re.match(emailRegex, email) is not None


def cohere_chat(user_message):
    try:
        # Load API key from a JSON file
        API = os.getenv("COHEREAPIKEY")

        # Initialize Cohere API client
        co = cohere.ClientV2(api_key=API)

        # Define the system message context
        system_message = """## Task and Context
        You are a medical professional providing advice to someone who might have skin cancer.

        ## Style Guide
        Respond in short, clear, and concise sentences. Provide only the necessary information and avoid over-explaining."""

        # Construct the list of messages
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

        # Generate the response from Cohere's API
        response = co.chat(model="command-r-plus-08-2024", messages=messages)

        # Extract the assistant's response
        assistant_message = response.message.content[0].text
        messages.append({"role": "assistant", "content": assistant_message})

        # print(assistant_message)  # Log the response (optional)

        return assistant_message
    except Exception as e:
        print(f"Error occurred: {e}")
        return "Sorry, there was an issue processing your message."


def upload_image(image_bytes, image_path, bucket):
    """Uploads an image to Firebase Storage and returns the public URL"""

    blob = bucket.blob(image_path)

    blob.upload_from_string(image_bytes, content_type="image/png")

    blob.make_public()

    return blob.public_url 


def download_model(LOCAL_MODEL_PATH, MODEL_URL):
    if not os.path.exists(LOCAL_MODEL_PATH):
        print(f"Downloading model from {MODEL_URL}...")
        response = requests.get(MODEL_URL, stream=True)
        if response.status_code == 200:
            with open(LOCAL_MODEL_PATH, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            print("Download complete.")
        else:
            raise Exception(f"Failed to download model. Status code: {response.status_code}")


def classification_model(file_name):
    IMAGE_SIZE1 = 224
    IMAGE_SIZE2 = 224

    MODEL_PATH = os.path.join(os.path.dirname(__file__), './trained_model.h5')
    MODEL_URL = os.getenv("MODELURL")

    download_model(MODEL_PATH, MODEL_URL)
    model = models.load_model(MODEL_PATH)

    # Load class names (adjust if saved separately)
    class_names = ['benign', 'malignant']  # Replace with actual class names

    # Preprocess image for prediction
    def preprocess_image(img_path):
        img = tf.keras.preprocessing.image.load_img(img_path, target_size=(IMAGE_SIZE1, IMAGE_SIZE2))  # load image
        img_array = tf.keras.preprocessing.image.img_to_array(img)  # convert to array
        img_array = tf.expand_dims(img_array, 0)  # create batch dimension
        return img_array


    def predict_image(model, img_path):
        img_array = preprocess_image(img_path)  # preprocess image from path
        prediction = model.predict(img_array)  # make prediction
        pred_class = class_names[np.argmax(prediction[0])]  # get class name
        confidence = round(100 * np.max(prediction[0]), 2)  # get confidence
        return pred_class, confidence

    # Run prediction
    img_path = file_name  # Replace with the image you want to predict
    predicted_class, confidence = predict_image(model, img_path)
    print(f"Predicted Class: {predicted_class}, Confidence: {confidence}%")

    return [predicted_class, confidence]
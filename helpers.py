import os
import secrets
import string
import re
import json
import cohere

from os import path

from functools import wraps
from flask import redirect, session, request, current_app

import os.path
import sqlite3
from sqlite3 import Error

from PIL import Image
import tensorflow as tf
from tensorflow.keras import models, layers
import matplotlib.pyplot as plt
import numpy as np
import os

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
    """Runs SQL Commands from a file"""
    db_path = "./static/sql/database.db"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        with open('./static/sql/' + sql_file, 'r') as file:
            sql_commands = file.read().split(';')
        for command in sql_commands:
            if command.strip():
                cursor.execute(command)
        conn.commit()
    except sqlite3.Error as e:
        print(f"SQL error: {e}")
    finally:
        conn.close()

# Creates SQL structures if they don't exist
def check_for_sql(app):
    """Ensures SQL structures exist"""
    db_path = "./static/sql/database.db"
    if not app.config.get("BEFORE_CHECK_EXECUTED"):
        if not os.path.exists(db_path):
            run_sql('schema.sql')
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

def cohere_chat(user_message):
    try:
        # Load API key from a JSON file
        with open('./static/cred.json', 'r') as file:
            data = json.load(file)['CohereAPIKey']

        # Initialize Cohere API client
        co = cohere.ClientV2(api_key=data)

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


def classification_model(file_name):

    IMAGE_SIZE1 = 224
    IMAGE_SIZE2 = 224
    BATCH_SIZE = 32
    CHANNELS  = 3
    EPOCHS = 50
    MODEL_PATH = './classification_model/trained_model.h5'  # Path to save/load the trained model

    # Data collection and preprocessing before training 

    # Load all images into dataset
    dataset = tf.keras.preprocessing.image_dataset_from_directory(
        "./classification_model/BM",  # Replace this with the actual path to your image folder
        shuffle=True,
        image_size=(IMAGE_SIZE1, IMAGE_SIZE2),
        batch_size=BATCH_SIZE
    )

    class_names = dataset.class_names

    # Get splits 80% train, 10% validate, 10% test
    def splits(ds, train_split=0.8, val_split=0.1, test_split=0.1, shuffle=True, shuffle_size=10000):
        if shuffle:
            ds = ds.shuffle(shuffle_size, seed=5)

        ds_size = len(ds)
        train_size = int(train_split * ds_size)
        val_size = int(val_split * ds_size)
        train_ds = ds.take(train_size)
        val_ds = ds.skip(train_size).take(val_size)
        test_ds = ds.skip(train_size).skip(val_size)

        return train_ds, val_ds, test_ds

    train_ds, val_ds, test_ds = splits(dataset)

    # Keep image in memory
    train_ds = train_ds.cache().shuffle(1000).prefetch(buffer_size=tf.data.AUTOTUNE)
    val_ds = val_ds.cache().shuffle(1000).prefetch(buffer_size=tf.data.AUTOTUNE)
    test_ds = test_ds.cache().shuffle(1000).prefetch(buffer_size=tf.data.AUTOTUNE)

    # Resize and rescale
    rr = tf.keras.Sequential([
        layers.Resizing(IMAGE_SIZE1, IMAGE_SIZE2),
        layers.Rescaling(1.0/255)
    ])

    # Data augmentation
    data_aug = tf.keras.Sequential([
        layers.RandomFlip("horizontal_and_vertical"),
        layers.RandomRotation(0.2)
    ])

    # BUILDING MODEL
    num_class = 2
    model = models.Sequential([
        rr,
        data_aug,
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, kernel_size=(3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, kernel_size=(3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.Dense(num_class, activation='softmax'),
    ])

    model.compile(
        optimizer='adam',
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=False),
        metrics=['accuracy']
    )

    # Check if the model is already trained and saved, if so, load it
    history = None
    if os.path.exists(MODEL_PATH):
        model = models.load_model(MODEL_PATH)
        print(f"Loaded model from {MODEL_PATH}")
    else:
        history = model.fit(
            train_ds,
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            verbose=1,
            validation_data=val_ds
        )

        # Save the trained model
        model.save(MODEL_PATH)
        print(f"Model trained and saved at {MODEL_PATH}")

    # Evaluate the model on the test dataset
    scores = model.evaluate(test_ds)
    print(scores)

    # Predicting on a new image
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

    # Provide path to the image you want to predict
    img_path = file_name  # Replace with the image you want to predict
    predicted_class, confidence = predict_image(model, img_path)
    print(f"Predicted Class: {predicted_class}, Confidence: {confidence}%")

    return [predicted_class, confidence]
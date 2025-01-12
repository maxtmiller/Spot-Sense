# imports and global constants
import tensorflow as tf
from tensorflow.keras import models, layers
import matplotlib.pyplot as plt
import numpy as np
import os

IMAGE_SIZE1 = 224
IMAGE_SIZE2 = 224
BATCH_SIZE = 32
CHANNELS  = 3
EPOCHS = 50
MODEL_PATH = 'trained_model.h5'  # Path to save/load the trained model

# Data collection and preprocessing before training 

# Load all images into dataset
dataset = tf.keras.preprocessing.image_dataset_from_directory(
    "BM",  # Replace this with the actual path to your image folder
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
img_path = 'download.png'  # Replace with the image you want to predict
predicted_class, confidence = predict_image(model, img_path)
print(f"Predicted Class: {predicted_class}, Confidence: {confidence}%")

# Display the image with prediction using Matplotlib
img = tf.keras.preprocessing.image.load_img(img_path, target_size=(IMAGE_SIZE1, IMAGE_SIZE2))

plt.imshow(img)
plt.title(f"Prediction: {predicted_class} with {confidence}% confidence")
plt.axis('off')
plt.show()

# [`SpotSense`](https://devpost.com/software/skin-analyzer)

SpotSense is a web app that helps you quickly assess potential skin cancer risks using AI. You upload or capture a photo through your webcam, and a TensorFlow trained neural network analyzes the image to classify it as potentially malignant or benign. Images are securely stored in an SQL database for future reference. If you need medical support, the built in Help section uses the Google Maps API to locate nearby hospitals, and a Cohere powered chatbot answers general questions about skin conditions. Google OAuth secures login and protects user data.

We built SpotSense to reduce the fear and uncertainty people feel when they notice a new mole or skin change. Many people delay action because they lack quick guidance. By combining machine learning, secure infrastructure, and accessible tools, SpotSense makes it easier to check your skin, get immediate feedback, and connect with professional care when needed.

## Technical Overview
- Frontend: HTML, CSS, Jinja
- Backend: Flask, Python, Javascript
- Libraries: Tensorflow, Keras, Google OAuth, Google Maps API, Pillow, Numpy
- Database: MySQL

## Next Steps
Next for SpotSense, we aim to enhance our AI model's accuracy by incorporating a broader dataset to improve predictions across diverse skin types and conditions. We plan to integrate telemedicine features, allowing users to connect directly with dermatologists for professional advice. Additionally, we’re working on a personalized health-tracking dashboard where users can monitor skin changes over time and receive tailored health tips. With future updates, we envision SpotSense becoming a comprehensive tool for proactive skin health management.

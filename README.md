# DeltaHacks XI:

## 💡Inspiration💡
We created this app because we saw how scary and confusing it can be for people who notice a new spot or mole and aren’t sure what it means. We wanted to give everyone an easy way to check their skin, find answers fast, and connect with medical help if needed. By combining AI with simple, user-friendly tools, we strive to make it less overwhelming to stay on top of your skin health and catch potential issues early—because a little peace of mind can make a big difference.

## 🔍 What it does 🔍
Meet SpotSense, a user-friendly web app that takes the guesswork out of checking for skin cancer. Upload or snap a photo through your webcam, and our TensorFlow model will analyze it to see if it might be malignant or benign. Your images are stored securely in an SQL database, and there’s even a “Help” section, powered by Google Maps that help find nearby hospitals. Need more guidance? Our Cohere-powered chatbot is on hand to answer questions about skin diseases, and Google OAuth keeps everything secure for a smooth experience.

## 🛠️ How we built it 🛠️
We built SpotSense by combining several powerful tools and frameworks to ensure accuracy and ease of use. At its core is a TensorFlow-trained model, which relies on neural networks and machine learning to analyze user-submitted or webcam-captured images and classify them as potentially malignant or benign. These images are stored in an SQL database for future review or follow-up. We also integrated a “Help” section that uses the Google Maps API to help users quickly locate hospitals if they need additional medical support, employing a Cohere-powered chatbot to answer general questions about skin diseases. Finally, we implemented Google OAuth to deliver a secure login experience, ensuring user data remains protected while offering a streamlined workflow.

## 🚧 Challenges we ran into 🚧
Finding a diverse, high-quality dataset for our TensorFlow model to accurately predict whether the image was malignant or benign.
Maintaining quick response times during the image analysis.
Storing user images and data in an SQL database securely, ensuring everything remains private and trustworthy.
Managing multiple services (Google Maps, Cohere chatbot, Google OAuth) introduced extra challenges and compatibility issues.

## 🏆 Accomplishments that we're proud of 🏆
We designed a simple, good-looking UI to help you focus on your health
We developed a TensorFlow model powered by advanced neural networks and machine learning techniques, enabling accurate classification of images as malignant or benign.
We integrated webcam captures and image uploads into a straightforward user flow, making skin checks simple and accessible.
Implemented several APIs and services into our project (Google Maps, Cohere, Google OAuth)

## 🧠 What we learned 🧠
How to efficiently use GitHub/Git for collaboration and part integration
How to use Tensorflow and Keras to create neural networks and deep learning models
Using SQL to store images in databases
Setting up webcam features
Using Google Maps API to retrieve routes to the nearest hospitals based on user address
Using Cohere API to create a friendly chatbot

## 🚀 What's Next for SpotSense? 🚀
Next for SpotSense, we aim to enhance our AI model's accuracy by incorporating a broader dataset to improve predictions across diverse skin types and conditions. We plan to integrate telemedicine features, allowing users to connect directly with dermatologists for professional advice. Additionally, we’re working on a personalized health-tracking dashboard where users can monitor skin changes over time and receive tailored health tips. With future updates, we envision SpotSense becoming a comprehensive tool for proactive skin health management.

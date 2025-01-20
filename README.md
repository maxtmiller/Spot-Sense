# DeltaHacks XI:

## 💡INSPIRATION BEHIND SPOTSNSE💡
We created this app because we saw how scary and confusing it can be for people who notice a new spot or mole and aren’t sure what it means. We wanted to give everyone an easy way to check their skin, find answers fast, and connect with medical help if needed. By combining AI with simple, user-friendly tools, we strive to make it less overwhelming to stay on top of your skin health and catch potential issues early—because a little peace of mind can make a big difference.

## 🔍 WHAT IS SPOTSENSE 🔍
Meet SpotSense, a user-friendly web app that takes the guesswork out of checking for skin cancer. Upload or snap a photo through your webcam, and our TensorFlow model will analyze it to see if it might be malignant or benign. Your images are stored securely in an SQL database, and there’s even a “Help” section, powered by Google Maps that help find nearby hospitals. Need more guidance? Our Cohere-powered chatbot is on hand to answer questions about skin diseases, and Google OAuth keeps everything secure for a smooth experience.

## 🛠️ HOW WE BUILT IT 🛠️
We built SpotSense by combining several powerful tools and frameworks to ensure accuracy and ease of use. At its core is a TensorFlow-trained model, which relies on neural networks and machine learning to analyze user-submitted or webcam-captured images and classify them as potentially malignant or benign. These images are stored in an SQL database for future review or follow-up. We also integrated a “Help” section that uses the Google Maps API to help users quickly locate hospitals if they need additional medical support, employing a Cohere-powered chatbot to answer general questions about skin diseases. Finally, we implemented Google OAuth to deliver a secure login experience, ensuring user data remains protected while offering a streamlined workflow.

## 🖥 TECHNOLOGIES USED 🖥
- Frontend: HTML, CSS, Jinja
- Backend: Flask, Python, Javascript
- Libraries: Tensorflow, Keras, Google OAuth, Google Maps API, Pillow, Numpy
- Database: MySQL

## 🚀 WHAT'S NEXT FOR SPOTSENSE 🚀
Next for SpotSense, we aim to enhance our AI model's accuracy by incorporating a broader dataset to improve predictions across diverse skin types and conditions. We plan to integrate telemedicine features, allowing users to connect directly with dermatologists for professional advice. Additionally, we’re working on a personalized health-tracking dashboard where users can monitor skin changes over time and receive tailored health tips. With future updates, we envision SpotSense becoming a comprehensive tool for proactive skin health management.

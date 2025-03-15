async function loadFirebaseConfig() {
    try {
        const response = await fetch("/firebase-config");
        const firebaseConfig = await response.json();

        // 🔹 Initialize Firebase dynamically
        firebase.initializeApp(firebaseConfig);
        console.log("Firebase Initialized:", firebaseConfig);
    } catch (error) {
        console.error("Error loading Firebase config:", error);
    }
}

async function googleLogin() {
    const response = await fetch("/firebase-config");
    const firebaseConfig = await response.json();

    const app = firebase.initializeApp(firebaseConfig);
    const auth = firebase.auth();

    const provider = new firebase.auth.GoogleAuthProvider();
    try {
        const result = await auth.signInWithPopup(provider);
        const user = result.user;

        // Get the ID token from Firebase user
        const idToken = await user.getIdToken();

        // Send ID token to backend for verification and login
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id_token: idToken })
        });

        const data = await response.json();
        if (response.ok) {
            console.log("Login successful:", data);
            window.location.href = "/";  // Redirect to home
        } else {
            console.error("Login failed:", data.error);
            document.getElementById("badEvent").innerText = data.error;
        }
    } catch (error) {
        console.error('Google login error:', error);
    }
}

// Load Firebase config on page load
window.onload = () => {
    loadFirebaseConfig();
};
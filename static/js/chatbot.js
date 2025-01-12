const inputField = document.getElementById("user-input");
const sendButton = document.getElementById("send-btn");

inputField.addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        sendButton.click();
    }
});

function sendMessage() {
    var userMessage = document.getElementById('user-input').value;
    if (userMessage.trim() === '') return;

    var chatBox = document.getElementById('chat-box');
    chatBox.innerHTML += '<div class="message user-message">' + userMessage + '</div>';
    document.getElementById('user-input').value = '';
    chatBox.scrollTop = chatBox.scrollHeight;

    fetch('/chatbot/message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage })
    })
    .then(response => response.json())
    .then(data => {
        var botMessage = data.response;
        chatBox.innerHTML += '<div class="message bot-message">' + botMessage + '</div>';
        chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
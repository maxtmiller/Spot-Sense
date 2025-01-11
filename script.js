function previewImage() {
    const fileInput = document.getElementById("imageUpload");
    const previewContainer = document.getElementById("imagePreview");
    const file = fileInput.files[0];
  
    if (file) {
      const reader = new FileReader();
  
      reader.onload = function (e) {
        previewContainer.innerHTML = `
          <img src="${e.target.result}" alt="Uploaded Image" style="max-width: 90%; max-height: 60vh;">
        `;
      };
  
      reader.readAsDataURL(file);
    } else {
      previewContainer.innerHTML = "";
    }
  }
  
  function openCamera() {
    const video = document.getElementById("cameraFeed");
    const captureButton = document.getElementById("captureButton");
  
    navigator.mediaDevices
      .getUserMedia({ video: true })
      .then((stream) => {
        video.style.display = "block";
        captureButton.style.display = "inline-block";
        video.srcObject = stream;
      })
      .catch((err) => {
        console.error("Camera access error:", err);
        alert("Unable to access the camera.");
      });
  }
  
  function capturePhoto() {
    const video = document.getElementById("cameraFeed");
    const canvas = document.getElementById("canvas");
    const previewContainer = document.getElementById("imagePreview");
  
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
  
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  
    const photo = canvas.toDataURL("image/png");
    previewContainer.innerHTML = `<img src="${photo}" alt="Captured Image" style="max-width: 90%; max-height: 60vh;">`;
  
    // Stop the camera
    const stream = video.srcObject;
    const tracks = stream.getTracks();
    tracks.forEach((track) => track.stop());
  
    video.style.display = "none";
    document.getElementById("captureButton").style.display = "none";
  }
  
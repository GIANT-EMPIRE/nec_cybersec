// staff_portal/static/staff_portal/js/camera.js
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const captured = document.getElementById('captured_image');

navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => { video.srcObject = stream; })
  .catch(err => console.error("Webcam error: ", err));

function capture() {
  canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
  captured.value = canvas.toDataURL('image/png');
  alert("Image Captured!");
}

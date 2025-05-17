const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const statusText = document.getElementById('status');

async function initCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        setTimeout(captureAndSend, 3000);
    } catch (err) {
        statusText.innerText = "Camera access denied.";
    }
}

function captureAndSend() {
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(blob => {
        const formData = new FormData();
        formData.append('image', blob, 'captured.jpg');

        fetch('/scan', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.redirect) {
                window.location.href = `/user/${data.user_id}`;
            } else {
                statusText.innerText = data.message;
            }
        });
    }, 'image/jpeg');
}

initCamera();

from flask import Flask, render_template, redirect, url_for, request, jsonify
import cv2
import face_recognition
import numpy as np
import os
import uuid
import base64
import re

app = Flask(__name__)
KNOWN_FACE_DIR = 'known_faces'
os.makedirs(KNOWN_FACE_DIR, exist_ok=True)

def load_known_faces():
    known_encodings = []
    known_names = []
    for file in os.listdir(KNOWN_FACE_DIR):
        if file.endswith('.npy'):
            encoding = np.load(os.path.join(KNOWN_FACE_DIR, file))
            known_encodings.append(encoding)
            known_names.append(file.replace('.npy', ''))
    return known_encodings, known_names

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/scan', methods=['POST'])
def scan_face():
    data = request.get_json()
    image_data = data.get('image')

    # Extract base64 string from data URL
    img_str = re.search(r'base64,(.*)', image_data).group(1)
    img_bytes = base64.b64decode(img_str)

    # Convert to numpy array and decode image
    nparr = np.frombuffer(img_bytes, np.uint8)
    img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    rgb_frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
    faces = face_recognition.face_encodings(rgb_frame)

    if faces:
        face_encoding = faces[0]
        known_encodings, known_names = load_known_faces()
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.45)

        if True in matches:
            matched_index = matches.index(True)
            name = known_names[matched_index]
            return jsonify({"redirect_url": url_for('account', name=name)})
        else:
            new_id = str(uuid.uuid4())
            np.save(os.path.join(KNOWN_FACE_DIR, f'{new_id}.npy'), face_encoding)
            cv2.imwrite(os.path.join(KNOWN_FACE_DIR, f'{new_id}.jpg'), img_np)
            return jsonify({"redirect_url": url_for('new_account', name=new_id)})

    return jsonify({"message": "No face detected. Please try again."})

@app.route('/account/<name>')
def account(name):
    return render_template('account.html', name=name)

@app.route('/new_account/<name>')
def new_account(name):
    return render_template('new_account.html', name=name)

if __name__ == '__main__':
    app.run(debug=True)

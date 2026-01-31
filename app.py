from flask import Flask, render_template, request, jsonify
import face_recognition
import os
import base64
import numpy as np
import cv2

app = Flask(__name__)

# Folder kung saan ise-save ang mga mukha
UPLOAD_FOLDER = 'known_faces'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- HOME PAGE ---
@app.route('/')
def home():
    return render_template('index.html')

# --- REGISTRATION API ---
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data['name']
    image_data = data['image'] # Base64 string

    # 1. Convert Base64 to Image File
    header, encoded = image_data.split(",", 1)
    img_bytes = base64.b64decode(encoded)
    
    # Save file as "Name.jpg" (e.g., "Bantay.jpg")
    file_path = os.path.join(UPLOAD_FOLDER, f"{name}.jpg")
    with open(file_path, "wb") as f:
        f.write(img_bytes)

    return jsonify({"status": "success", "message": f"Pet {name} Registered!"})

# --- SCANNING / AI MATCHING API ---
@app.route('/scan_face', methods=['POST'])
def scan_face():
    data = request.json
    live_image_data = data['image']

    # 1. Process Live Image
    header, encoded = live_image_data.split(",", 1)
    img_bytes = base64.b64decode(encoded)
    nparr = np.frombuffer(img_bytes, np.uint8)
    live_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Convert to RGB (Required by face_recognition)
    rgb_live_img = cv2.cvtColor(live_img, cv2.COLOR_BGR2RGB)
    
    # Get encodings of live image
    live_encodings = face_recognition.face_encodings(rgb_live_img)

    if len(live_encodings) == 0:
        return jsonify({"match": False, "message": "No face detected"})

    live_face_encoding = live_encodings[0]

    # 2. Compare against SAVED images in folder
    found_match = False
    matched_name = ""
    matched_photo = ""

    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            # Load saved image
            saved_img_path = os.path.join(UPLOAD_FOLDER, filename)
            saved_image = face_recognition.load_image_file(saved_img_path)
            saved_encodings = face_recognition.face_encodings(saved_image)

            if len(saved_encodings) > 0:
                saved_encoding = saved_encodings[0]
                
                # THE REAL AI CHECK (Tolerance: Lower is stricter)
                match = face_recognition.compare_faces([saved_encoding], live_face_encoding, tolerance=0.5)

                if match[0]:
                    found_match = True
                    matched_name = os.path.splitext(filename)[0] # Get name from filename
                    # Read the file to send back to UI
                    with open(saved_img_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        matched_photo = "data:image/jpeg;base64," + encoded_string
                    break 

    if found_match:
        return jsonify({
            "match": True, 
            "name": matched_name, 
            "owner": "Verified Owner", # Placeholder
            "photo": matched_photo
        })
    else:
        return jsonify({"match": False, "message": "Unknown Pet"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
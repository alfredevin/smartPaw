from flask import Flask, render_template, request, jsonify
import os
import base64
import numpy as np
import cv2
import sqlite3
import datetime

app = Flask(__name__)

# Folder settings
UPLOAD_FOLDER = 'known_faces'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Face Detector (Strict Mode para iwas pader)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def init_db():
    conn = sqlite3.connect('smartpaw.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owner TEXT NOT NULL,
            address TEXT NOT NULL,
            filename TEXT NOT NULL,
            date_registered TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

# --- HELPER: STRICT DETECTION ---
def has_face(image_data):
    try:
        header, encoded = image_data.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Strict settings para iwas false positive
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        return len(faces) > 0
    except:
        return False

# --- GET PETS (Added ID for deletion) ---
@app.route('/get_pets', methods=['GET'])
def get_pets():
    conn = sqlite3.connect('smartpaw.db')
    c = conn.cursor()
    c.execute("SELECT * FROM pets ORDER BY id DESC")
    pets = c.fetchall()
    conn.close()
    
    pet_list = []
    for p in pets:
        img_path = os.path.join(UPLOAD_FOLDER, p[4])
        img_str = "/static/default.jpg" # Fallback
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                img_str = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode('utf-8')
        
        pet_list.append({
            "id": p[0],   # IMPORTANT: ID for deleting
            "name": p[1],
            "owner": p[2],
            "address": p[3],
            "photo": img_str
        })
    
    return jsonify(pet_list)

# --- NEW: DELETE FUNCTION ---
@app.route('/delete_pet/<int:id>', methods=['DELETE'])
def delete_pet(id):
    try:
        conn = sqlite3.connect('smartpaw.db')
        c = conn.cursor()
        
        # Optional: Delete also the image file if you want to save space
        c.execute("SELECT filename FROM pets WHERE id = ?", (id,))
        file_record = c.fetchone()
        if file_record:
            try:
                os.remove(os.path.join(UPLOAD_FOLDER, file_record[0]))
            except:
                pass # Ignore if file not found

        c.execute("DELETE FROM pets WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Record deleted!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        if not has_face(data['image']):
            return jsonify({"status": "error", "message": "No face detected. Please ensure good lighting."})

        conn = sqlite3.connect('smartpaw.db')
        c = conn.cursor()
        
        filename = f"{data['name']}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        header, encoded = data['image'].split(",", 1)
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(encoded))

        c.execute("INSERT INTO pets (name, owner, address, filename, date_registered) VALUES (?, ?, ?, ?, ?)",
                  (data['name'], data['owner'], data['address'], filename, datetime.datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        conn.close()

        return jsonify({"status": "success", "message": "Registered Successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/scan_face', methods=['POST'])
def scan_face():
    try:
        data = request.json
        if not has_face(data['image']):
            return jsonify({"match": False, "message": "Searching..."})

        conn = sqlite3.connect('smartpaw.db')
        c = conn.cursor()
        c.execute("SELECT * FROM pets ORDER BY id DESC LIMIT 1")
        pet = c.fetchone()
        conn.close()

        if pet:
            img_path = os.path.join(UPLOAD_FOLDER, pet[4])
            img_str = ""
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    img_str = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode('utf-8')

            return jsonify({
                "match": True,
                "data": {
                    "name": pet[1],
                    "owner": pet[2],
                    "address": pet[3],
                    "photo": img_str
                }
            })
        else:
            return jsonify({"match": False, "message": "No data yet"})
            
    except Exception as e:
        return jsonify({"match": False, "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
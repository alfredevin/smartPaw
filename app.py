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

# Face Detector (OpenCV)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def init_db():
    conn = sqlite3.connect('smartpaw.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, owner TEXT NOT NULL,
        address TEXT NOT NULL, filename TEXT NOT NULL, date_registered TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- REAL FACE MATCHING LOGIC ---
def compare_faces(captured_img_base64, stored_img_path):
    try:
        # 1. Load captured image from browser
        header, encoded = captured_img_base64.split(",", 1)
        nparr = np.frombuffer(base64.b64decode(encoded), np.uint8)
        img1 = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        img1 = cv2.resize(img1, (200, 200)) 

        # 2. Load stored image from folder
        img2 = cv2.imread(stored_img_path, cv2.IMREAD_GRAYSCALE)
        if img2 is None: return 0
        img2 = cv2.resize(img2, (200, 200))

        # 3. Calculate Correlation (Template Matching)
        res = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        
        return max_val # Returns 0 to 1
    except:
        return 0

@app.route('/')
def home():
    return render_template('index.html')

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
        img_str = ""
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                img_str = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode('utf-8')
        pet_list.append({"id": p[0], "name": p[1], "owner": p[2], "address": p[3], "photo": img_str})
    return jsonify(pet_list)

@app.route('/delete_pet/<int:id>', methods=['DELETE'])
def delete_pet(id):
    try:
        conn = sqlite3.connect('smartpaw.db')
        c = conn.cursor()
        c.execute("DELETE FROM pets WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success"})
    except:
        return jsonify({"status": "error"})

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        filename = f"{data['name']}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        header, encoded = data['image'].split(",", 1)
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(encoded))
        conn = sqlite3.connect('smartpaw.db')
        c = conn.cursor()
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
        captured_image = data['image']
        
        conn = sqlite3.connect('smartpaw.db')
        c = conn.cursor()
        c.execute("SELECT * FROM pets")
        all_pets = c.fetchall()
        conn.close()

        best_match = None
        highest_score = 0
        threshold = 0.60 # Sensitivity Level

        for pet in all_pets:
            file_path = os.path.join(UPLOAD_FOLDER, pet[4])
            score = compare_faces(captured_image, file_path)
            if score > highest_score:
                highest_score = score
                best_match = pet

        if best_match and highest_score >= threshold:
            img_path = os.path.join(UPLOAD_FOLDER, best_match[4])
            with open(img_path, "rb") as f:
                img_str = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode('utf-8')
            return jsonify({
                "match": True,
                "score": round(highest_score * 100, 2),
                "data": {"name": best_match[1], "owner": best_match[2], "address": best_match[3], "photo": img_str}
            })
        
        return jsonify({"match": False, "message": "No match found."})
    except Exception as e:
        return jsonify({"match": False, "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
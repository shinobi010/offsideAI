from flask import Blueprint, request, jsonify
import os
import cv2
import numpy as np
from werkzeug.utils import secure_filename
from ultralytics import YOLO

routes_bp = Blueprint('routes', __name__)

# Load YOLO model
model = YOLO("yolov8n.pt")  # Make sure you have this file

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@routes_bp.route("/upload", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Perform YOLO detection
        results = model(filepath)

        players = []
        ball = None

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])  # Class ID
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates

                # Assume class 0 is "player" and class 1 is "ball" (you may need to adjust)
                if cls == 0:  # Player
                    players.append({"x": (x1 + x2) // 2, "y": y2})  # Bottom center of player
                 # Ball
                    ball = {"x": (x1 + x2) // 2, "y": (y1 + y2) // 2}  # Ball center

        # Determine if offside
        offside_result = check_offside(players, ball)

        return jsonify({"filename": filename, "players": players, "ball": ball, "offside": offside_result})

    return jsonify({"error": "Invalid file type"}), 400

def check_offside(players, ball):
    if not players or not ball:
        return "Not enough data"

    # Sort players by Y-coordinate (assuming Y is vertical field position)
    players = sorted(players, key=lambda p: p["y"])

    # The second-to-last defender (defenders are closer to own goal, so we take the 2nd one)
    if len(players) < 2:
        return "Not enough players detected"

    second_last_defender = players[-2]  # Second-to-last defender is the second closest to the goal

    # Check if any attacker is offside
    for player in players:
        if player["y"] < second_last_defender["y"] and player["x"] > ball["x"]:  # Offside condition
            return True

    return False

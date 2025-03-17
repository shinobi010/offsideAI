from flask import Blueprint, request, jsonify
import os
import time
import cv2
import numpy as np
from werkzeug.utils import secure_filename
from ultralytics import YOLO
from multiprocessing import Process, Pipe, Queue
from threading import Thread, Lock, Semaphore

routes_bp = Blueprint('routes', __name__)

# Load YOLO model
model = YOLO("yolov8n.pt")  # Make sure you have this file

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_offside(players, ball):
    if not players or not ball:
        return "Not enough data"

    players = sorted(players, key=lambda p: p["y"])

    if len(players) < 2:
        return "Not enough players detected"

    second_last_defender = players[-2]
    
    for player in players:
        if player["y"] < second_last_defender["y"] and player["x"] > ball["x"]:
            return True
    
    return False

# ------------------------ MONOPROCESS ------------------------
@routes_bp.route("/upload_monoprocess", methods=["POST"])
def upload_monoprocess():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        start_time = time.time()
        results = model(filepath)
        
        players = []
        ball = None

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                if cls == 0:
                    players.append({"x": (x1 + x2) // 2, "y": y2})
                    ball = {"x": (x1 + x2) // 2, "y": (y1 + y2) // 2}
        
        offside_result = check_offside(players, ball)
        execution_time = time.time() - start_time
        
        return jsonify({"filename": filename, "players": players, "ball": ball, "offside": offside_result, "execution_time": execution_time})
    
    return jsonify({"error": "Invalid file type"}), 400

# ------------------------ MULTIPROCESS ------------------------
def process_image(pipe, filepath):
    results = model(filepath)
    players, ball = [], None
    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            if cls == 0:
                players.append({"x": (x1 + x2) // 2, "y": y2})
                ball = {"x": (x1 + x2) // 2, "y": (y1 + y2) // 2}
    pipe.send((players, ball))
    pipe.close()

@routes_bp.route("/upload_multiprocess", methods=["POST"])
def upload_multiprocess():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        parent_conn, child_conn = Pipe()
        start_time = time.time()
        p = Process(target=process_image, args=(child_conn, filepath))
        p.start()
        players, ball = parent_conn.recv()
        p.join()
        
        offside_result = check_offside(players, ball)
        execution_time = time.time() - start_time
        
        return jsonify({"filename": filename, "players": players, "ball": ball, "offside": offside_result, "execution_time": execution_time})
    
    return jsonify({"error": "Invalid file type"}), 400

# ------------------------ MULTITHREADING WITH SEMAPHORE ------------------------
semaphore = Semaphore(1)  # Limit to 1 thread accessing the critical section
queue = Queue()  # Queue for producer-consumer
offside_result = None  # Variable to store the offside result

def producer(filepath):
    results = model(filepath)
    players, ball = [], None
    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            if cls == 0:
                players.append({"x": (x1 + x2) // 2, "y": y2})
                ball = {"x": (x1 + x2) // 2, "y": (y1 + y2) // 2}
    queue.put((players, ball))

def consumer():
    global offside_result
    while True:
        players, ball = queue.get()
        if players is None and ball is None:  # Stop signal
            break
        offside_result = check_offside(players, ball)  # Store the offside result
        print(f"Offside check result: {offside_result}")
        queue.task_done()

@routes_bp.route("/upload_multithread", methods=["POST"])
def upload_multithread():
    global offside_result
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        start_time = time.time()
        consumer_thread = Thread(target=consumer)
        consumer_thread.start()

        with semaphore:  # Ensure only one thread accesses this block at a time
            producer(filepath)
        
        # Signal the consumer to stop
        queue.put((None, None))
        consumer_thread.join()

        execution_time = time.time() - start_time
        
        # Include the offside result in the response
        return jsonify({
            "filename": filename,
            "offside": offside_result,
            "execution_time": execution_time
        })
    
    return jsonify({"error": "Invalid file type"}), 400
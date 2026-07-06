# logic.py

import cv2
import numpy as np
import sqlite3
import time
import os

print("LOGIC FILE LOADED")

DB_FILE = "morphic.db"
IMAGE_FOLDER = "captured"

GRID_SIZE = 8

# Easier detection values
MIN_SPIKE_AREA = 40
MIN_SPIKES_REQUIRED = 1


# ==========================
# DATABASE
# ==========================
def init_db():

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS keys(
        location TEXT PRIMARY KEY,
        data TEXT
    )
    """)

    conn.commit()
    conn.close()


# ==========================
# CAMERA
# ==========================
def capture_frame():

    cap = None

    # Try external camera first
    for cam in [1, 0, 2, 3]:

        temp = cv2.VideoCapture(cam)

        if temp.isOpened():
            cap = temp
            print("Using camera:", cam)
            break

    if cap is None:
        return None

    time.sleep(2)

    frame = None

    for _ in range(10):
        ret, img = cap.read()
        if ret:
            frame = img

    cap.release()

    return frame


# ==========================
# IMAGE PROCESSING
# ==========================
def get_spikes(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    thresh = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11,
        2
    )

    kernel = np.ones((3, 3), np.uint8)

    thresh = cv2.morphologyEx(
        thresh,
        cv2.MORPH_CLOSE,
        kernel
    )

    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    centers = []

    for cnt in contours:

        area = cv2.contourArea(cnt)

        if area > MIN_SPIKE_AREA:

            M = cv2.moments(cnt)

            if M["m00"] != 0:

                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])

                centers.append((cx, cy))

    return centers


# ==========================
# GRID HASH
# ==========================
def get_bitstring(points, width=640, height=480):

    grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)

    for x, y in points:

        gx = int(x / (width / GRID_SIZE))
        gy = int(y / (height / GRID_SIZE))

        if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
            grid[gy, gx] = 1

    return "".join(map(str, grid.flatten()))


def hamming(a, b):
    return sum(x != y for x, y in zip(a, b))


# ==========================
# REGISTER
# ==========================
def register_key(location):

    init_db()

    frame = capture_frame()

    if frame is None:
        return {
            "status": "error",
            "message": "Camera not detected"
        }

    spikes = get_spikes(frame)

    if len(spikes) < MIN_SPIKES_REQUIRED:
        return {
            "status": "error",
            "message": "Show clearer object to camera"
        }

    bits = get_bitstring(spikes)

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO keys(location,data)
    VALUES(?,?)
    """, (location, bits))

    conn.commit()
    conn.close()

    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)

    filename = f"{location}_{int(time.time())}.jpg"
    cv2.imwrite(os.path.join(IMAGE_FOLDER, filename), frame)

    return {
        "status": "success",
        "message": "Key Registered Successfully",
        "spikes": len(spikes)
    }


# ==========================
# AUTHENTICATE
# ==========================
def authenticate_key(location):

    init_db()

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(
        "SELECT data FROM keys WHERE location=?",
        (location,)
    )

    row = cur.fetchone()

    conn.close()

    if row is None:
        return {
            "status": "error",
            "message": "No key found"
        }

    stored_bits = row[0]

    frame = capture_frame()

    if frame is None:
        return {
            "status": "error",
            "message": "Camera not detected"
        }

    spikes = get_spikes(frame)

    bits = get_bitstring(spikes)

    dist = hamming(bits, stored_bits)

    match = round(
        ((64 - dist) / 64) * 100,
        2
    )

    if match >= 60:
        return {
            "status": "success",
            "message": "Access Granted",
            "match_percent": match
        }

    return {
        "status": "error",
        "message": "Access Denied",
        "match_percent": match
    }
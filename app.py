# main.py  (PART 1/2)

import os
import re
import json
import sqlite3
from datetime import datetime, date
from werkzeug.utils import secure_filename

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, send_from_directory, session
)
from flask_cors import CORS
from flask_socketio import SocketIO

from dotenv import load_dotenv
from groq import Groq


BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # app.py ka folder
DB_PATH = os.path.join(BASE_DIR, 'jeevansathi.db')     # DB file ka path

# -------------------- App Config --------------------
load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", "change_this_secret")
app.config["UPLOAD_FOLDER"] = "uploads"

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# -------------------- Groq Client (Kundli) --------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# -------------------- Helpers --------------------
def get_db():
    conn = sqlite3.connect("jeevansathi.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Bride
    c.execute("""
        CREATE TABLE IF NOT EXISTS Bride_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            email_id TEXT,
            phone_number TEXT,
            country TEXT,
            state TEXT,
            city TEXT,
            address TEXT,
            diet TEXT,
            complexion TEXT,
            height TEXT,
            weight TEXT,
            image TEXT,
            video TEXT,
            username TEXT,
            password TEXT,
            manglik TEXT,
            date_of_birth TEXT,
            age INTEGER,
            profession TEXT,
            package TEXT,
            education TEXT,
            likes TEXT,
            dislikes TEXT
        )
    """)

    # Groom
    c.execute("""
        CREATE TABLE IF NOT EXISTS Groom_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            email_id TEXT,
            phone_number TEXT,
            country TEXT,
            state TEXT,
            city TEXT,
            address TEXT,
            diet TEXT,
            complexion TEXT,
            height TEXT,
            weight TEXT,
            image TEXT,
            video TEXT,
            username TEXT,
            password TEXT,
            manglik TEXT,
            date_of_birth TEXT,
            age INTEGER,
            profession TEXT,
            package TEXT,
            education TEXT,
            likes TEXT,
            dislikes TEXT
        )
    """)

    # Requests  (keep both columns for backward-compat)
    c.execute("""
        CREATE TABLE IF NOT EXISTS Requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            status TEXT,           -- new unified column
            status_sender TEXT     -- legacy support
        )
    """)

    # Messages
    c.execute("""
        CREATE TABLE IF NOT EXISTS Messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            message TEXT NOT NULL,
            room_id TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
init_db()

# -------------------- Static Uploads --------------------
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# -------------------- Home --------------------
@app.route("/")
def home():
    return render_template("final.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/membership")
def membership():
    return render_template("subs.html")

@app.route("/contact")
def contact():
    return render_template("footer.html")

@app.route("/register")
def register():
    return render_template("index.html")

@app.route("/kundli")
def kundli():
    return render_template("kundli.html")

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/faqs")
def faqs():
    return render_template("faqs.html")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/footer")
def footer():
    return render_template("footer.html")
# -------------------- Create Profile: Bride --------------------
@app.route("/create-profile-bride", methods=["GET", "POST"])
def create_bride_profile():
    if request.method == "POST":
        form = request.form.to_dict()
        username = form.get("username", "").strip()

        # Age auto-calc
        age = None
        dob_str = form.get("dob")
        if dob_str:
            try:
                b = date.fromisoformat(dob_str)
                t = date.today()
                age = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
            except Exception:
                age = None

        # User folder
        user_dir = os.path.join(app.config["UPLOAD_FOLDER"], username)
        os.makedirs(user_dir, exist_ok=True)

        # Photos
        photos = request.files.getlist("images[]")
        photo_rel_paths = []
        for p in photos:
            if p and p.filename:
                fn = secure_filename(p.filename)
                p.save(os.path.join(user_dir, fn))
                photo_rel_paths.append(os.path.join(username, fn).replace("\\", "/"))

        # Video
        video = request.files.get("video_introduction")
        video_rel = None
        if video and video.filename:
            vfn = secure_filename(video.filename)
            video.save(os.path.join(user_dir, vfn))
            video_rel = os.path.join(username, vfn).replace("\\", "/")

        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO Bride_profile (
                full_name, email_id, phone_number, country, state, city, address, diet, complexion,
                height, weight, image, video, username, password, manglik, date_of_birth, age,
                profession, package, education, likes, dislikes
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            form.get("full_name"), form.get("email"), form.get("phone"),
            form.get("country"), form.get("state"), form.get("city"),
            form.get("address"), form.get("diet"), form.get("complexion"),
            form.get("height"), form.get("weight"),
            ",".join(photo_rel_paths), video_rel, username, form.get("password"),
            form.get("manglik"), form.get("dob"), age,
            form.get("profession"), form.get("package"), form.get("education"),
            form.get("likes"), form.get("dislikes")
        ))
        conn.commit()
        conn.close()

        flash("Bride profile created successfully!")
        return redirect(url_for("create_bride_profile"))

    return render_template("create-profile-bride.html")

# -------------------- Create Profile: Groom --------------------
@app.route("/create-profile-groom", methods=["GET", "POST"])
def create_groom_profile():
    if request.method == "POST":
        form = request.form.to_dict()
        username = form.get("username", "").strip()

        user_dir = os.path.join(app.config["UPLOAD_FOLDER"], username)
        os.makedirs(user_dir, exist_ok=True)

        photos = request.files.getlist("images[]")
        photo_rel_paths = []
        for p in photos:
            if p and p.filename:
                fn = secure_filename(p.filename)
                p.save(os.path.join(user_dir, fn))
                photo_rel_paths.append(os.path.join(username, fn).replace("\\", "/"))

        video = request.files.get("video_introduction")
        video_rel = None
        if video and video.filename:
            vfn = secure_filename(video.filename)
            video.save(os.path.join(user_dir, vfn))
            video_rel = os.path.join(username, vfn).replace("\\", "/")

        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO Groom_profile (
                full_name, email_id, phone_number, country, state, city, address, diet, complexion,
                height, weight, image, video, username, password, manglik, date_of_birth, age,
                profession, package, education, likes, dislikes
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            form.get("full_name"), form.get("email"), form.get("phone"),
            form.get("country"), form.get("state"), form.get("city"),
            form.get("address"), form.get("diet"), form.get("complexion"),
            form.get("height"), form.get("weight"),
            ",".join(photo_rel_paths), video_rel, username, form.get("password"),
            form.get("manglik"), form.get("dob"), form.get("age"),
            form.get("profession"), form.get("package"), form.get("education"),
            form.get("likes"), form.get("dislikes")
        ))
        conn.commit()
        conn.close()

        flash("Groom profile created successfully!")
        return redirect(url_for("create_groom_profile"))

    return render_template("create-profile-groom.html")

# -------------------- Login (Bride/Groom) --------------------
@app.route("/bride-login", methods=["POST"])
def bride_login():
    username = request.json.get("username", "").strip()
    password = request.json.get("password", "").strip()
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required!"})

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM Bride_profile WHERE username=? AND password=?", (username, password))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"success": False, "message": "Invalid username or password!"})

    profile = dict(row)
    # image field is CSV of relative paths
    first_image = (profile.get("image") or "").split(",")[0].strip()
    profile_out = {
        "full_name": profile.get("full_name"),
        "email_id": profile.get("email_id"),
        "phone_number": profile.get("phone_number"),
        "country": profile.get("country"),
        "state": profile.get("state"),
        "city": profile.get("city"),
        "address": profile.get("address"),
        "diet": profile.get("diet"),
        "complexion": profile.get("complexion"),
        "height": profile.get("height"),
        "weight": profile.get("weight"),
        "image": url_for("uploaded_file", filename=first_image) if first_image else "",
        "username": profile.get("username"),
        "manglik": profile.get("manglik"),
        "date_of_birth": profile.get("date_of_birth"),
        "age": profile.get("age"),
        "profession": profile.get("profession"),
        "package": profile.get("package"),
        "education": profile.get("education"),
        "likes": profile.get("likes"),
        "dislikes": profile.get("dislikes"),
    }
    session["bride_profile"] = profile_out
    return jsonify({"success": True, "profile": profile_out})

@app.route("/groom-login", methods=["POST"])
def groom_login():
    username = request.json.get("username", "").strip()
    password = request.json.get("password", "").strip()
    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required!"})

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM Groom_profile WHERE username=? AND password=?", (username, password))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"success": False, "message": "Invalid username or password!"})

    profile = dict(row)
    first_image = (profile.get("image") or "").split(",")[0].strip()
    profile_out = {
        "full_name": profile.get("full_name"),
        "email_id": profile.get("email_id"),
        "phone_number": profile.get("phone_number"),
        "country": profile.get("country"),
        "state": profile.get("state"),
        "city": profile.get("city"),
        "address": profile.get("address"),
        "diet": profile.get("diet"),
        "complexion": profile.get("complexion"),
        "height": profile.get("height"),
        "weight": profile.get("weight"),
        "image": url_for("uploaded_file", filename=first_image) if first_image else "",
        "username": profile.get("username"),
        "date_of_birth": profile.get("date_of_birth"),
        "age": profile.get("age"),
        "profession": profile.get("profession"),
        "package": profile.get("package"),
        "education": profile.get("education"),
        "likes": profile.get("likes"),
        "dislikes": profile.get("dislikes"),
    }
    session["groom_profile"] = profile_out
    return jsonify({"success": True, "profile": profile_out})

# -------------------- Profile Views (Cards + Requests state) --------------------
def _images_list(csv):
    if not csv:
        return []
    out = []
    for p in csv.split(","):
        p = p.strip().replace("\\", "/")
        if p:
            out.append(url_for("uploaded_file", filename=p))
    return out

@app.route("/bride-profile/<username>")
def bride_profile(username):
    # Connect to the database and fetch the bride's profile
    conn = sqlite3.connect("jeevansathi.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Bride_profile WHERE username = ?", (username,))
    profile = cursor.fetchone()

    # Fetch all groom profiles
    cursor.execute("SELECT * FROM Groom_profile")
    grooms = cursor.fetchall()

    # Fetch all requests where the session username is either Sender or Receiver
    cursor.execute("SELECT * FROM Requests WHERE sender = ? OR receiver = ?", (username, username))
    requests = cursor.fetchall()
    conn.close()

    if profile:
        # Map bride profile details to a dictionary
        profile_data = {
            "full_name": profile[1],
            "email_id": profile[2],
            "phone_number": profile[3],
            "country": profile[4],
            "state": profile[5],
            "city": profile[6],
            "address": profile[7],
            "diet": profile[8],
            "complexion": profile[9],
            "height": profile[10],
            "weight": profile[11],
            "image": profile[12].split(",")[0].replace("\\", "/"),  # Normalize path to use forward slashes
            "username": profile[14],
            "manglik": profile[16],
            "date_of_birth": profile[17],
            "age": profile[18],
            "profession": profile[19],
            "package": profile[20],
            "education": profile[21],
            "likes": profile[22],
            "dislikes": profile[23],
        }

        # Map groom profiles to a list of dictionaries
        groom_profiles = []
        for groom in grooms:
            groom_data = {
                "full_name": groom[1],
                "country": groom[4],
                "state": groom[5],
                "city": groom[6],
                "diet": groom[8],
                "complexion": groom[9],
                "height": groom[10],
                "weight": groom[11],
                "manglik": groom[16],
                "date_of_birth": groom[17],
                "age": groom[18],
                "profession": groom[19],
                "package": groom[20],
                "education": groom[21],
                "likes": groom[22],
                "dislikes": groom[23],
                "image": groom[12].split(",")[0].replace("\\", "/"),  # Normalize
                "images": [url_for('uploaded_file', filename=img.replace("\\", "/")) for img in groom[12].split(",") if img],
                "username": groom[14],
                "video": groom[13].replace("\\", "/") if groom[13] else None,  # Normalize video path if exists
                "Sender_status": None,
                "Send_Or_Receive": None,
            }

            # Check requests for the current groom
            for request in requests:
                if request[1] == username and request[2] == groom[14]:  # Session username is Sender
                    groom_data["Sender_status"] = request[3]
                    groom_data["Send_Or_Receive"] = "Sender"
                elif request[2] == username and request[1] == groom[14]:  # Session username is Receiver
                    groom_data["Sender_status"] = request[3]
                    groom_data["Send_Or_Receive"] = "Receiver"
                
            print("here is the groom data:", groom_data)
            groom_profiles.append(groom_data)

        # Store bride profile data in the session
        session['bride_profile'] = profile_data

        return render_template("bride-profile.html", profile=profile_data, grooms=groom_profiles)
    else:
        flash("Profile not found!")
        return redirect(url_for("home"))


@app.route("/groom-profile/<username>")
def groom_profile(username):
    # Connect to the database and fetch the groom's profile
    conn = sqlite3.connect("jeevansathi.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Groom_profile WHERE username = ?", (username,))
    profile = cursor.fetchone()

    # Fetch all bride profiles
    cursor.execute("SELECT * FROM Bride_profile")
    brides = cursor.fetchall()

    # Fetch all requests where the session username is either Sender or Receiver
    cursor.execute("SELECT * FROM Requests WHERE sender = ? OR receiver = ?", (username, username))
    requests = cursor.fetchall()
    conn.close()

    if profile:
        # Map groom profile details to a dictionary
        profile_data = {
            "full_name": profile[1],
            "email_id": profile[2],
            "phone_number": profile[3],
            "country": profile[4],
            "state": profile[5],
            "city": profile[6],
            "address": profile[7],
            "diet": profile[8],
            "complexion": profile[9],
            "height": profile[10],
            "weight": profile[11],
            "image": profile[12].split(",")[0].replace("\\", "/"),  # Normalize path to use forward slashes
            "username": profile[14],
            "manglik": profile[16],
            "date_of_birth": profile[17],
            "age": profile[18],
            "profession": profile[19],
            "package": profile[20],
            "education": profile[21],
            "likes": profile[22],
            "dislikes": profile[23],
        }

        # Map bride profiles to a list of dictionaries
        bride_profiles = []
        for bride in brides:
            bride_data = {
                "full_name": bride[1],
                "country": bride[4],
                "state": bride[5],
                "city": bride[6],
                "diet": bride[8],
                "complexion": bride[9],
                "height": bride[10],
                "weight": bride[11],
                "manglik": bride[16],
                "date_of_birth": bride[17],
                "age": bride[18],
                "profession": bride[19],
                "package": bride[20],
                "education": bride[21],
                "likes": bride[22],
                "dislikes": bride[23],
                "image": bride[12].split(",")[0].replace("\\", "/"),  # Normalize
                "images": [url_for('uploaded_file', filename=img.replace("\\", "/")) for img in bride[12].split(",") if img],
                "username": bride[14],
                "video": bride[13].replace("\\", "/") if bride[13] else None,  # Normalize video path if exists
                "Sender_status": None,
                "Send_Or_Receive": None,
            }

            # Check requests for the current bride
            for request in requests:
                if request[1] == username and request[2] == bride[14]:  # Session username is Sender
                    bride_data["Sender_status"] = request[3]
                    bride_data["Send_Or_Receive"] = "Sender"
                elif request[2] == username and request[1] == bride[14]:  # Session username is Receiver
                    bride_data["Sender_status"] = request[3]
                    bride_data["Send_Or_Receive"] = "Receiver"

            bride_profiles.append(bride_data)

        # Store groom profile data in the session
        session['groom_profile'] = profile_data

        return render_template("groom-profile.html", profile=profile_data, brides=bride_profiles)
    else:
        flash("Profile not found!")
        return redirect(url_for("home"))

# -------------------- Complete Profiles --------------------
@app.route("/groom-complete-profile/<username>/<viewer>")
def groom_complete_profile(username, viewer):
    print("here is the username:", username)
    print("here is the viewer:", viewer)

    conn = sqlite3.connect("jeevansathi.db")
    cursor = conn.cursor()

    # Fetch the viewer's profile
    cursor.execute("SELECT * FROM Bride_profile WHERE username = ?", (viewer,))
    profile = cursor.fetchone()
    print("here is the profile:", profile)
    if profile:
        # Map viewer profile details to a dictionary
        profile_data = {
            "full_name": profile[1],
            "email_id": profile[2],
            "phone_number": profile[3],
            "country": profile[4],
            "state": profile[5],
            "city": profile[6],
            "address": profile[7],
            "diet": profile[8],
            "complexion": profile[9],
            "height": profile[10],
            "weight": profile[11],
            "image": profile[12].split(",")[0].replace("\\", "/"),  # Normalize path to use forward slashes
            "username": profile[14],
            "manglik": profile[16],
            "date_of_birth": profile[17],
            "age": profile[18],
            "profession": profile[19],
            "package": profile[20],
            "education": profile[21],
            "likes": profile[22],
            "dislikes": profile[23],
        }

    # Fetch the groom's profile
    cursor.execute("SELECT * FROM Groom_profile WHERE username = ?", (username,))
    groom = cursor.fetchone()
    conn.close()

    if groom:
        # Map groom profile details to a dictionary
        groom_profile = {
            "full_name": groom[1],
            "email_id": groom[2],
            "phone_number": groom[3],
            "country": groom[4],
            "state": groom[5],
            "city": groom[6],
            "address": groom[7],
            "diet": groom[8],
            "complexion": groom[9],
            "height": groom[10],
            "weight": groom[11],
            "images": [url_for('uploaded_file', filename=img.replace("\\", "/")) for img in groom[12].split(",") if img],
            "video": groom[13].replace("\\", "/") if groom[13] else None,
            "username": groom[14],
            "manglik": groom[16],
            "date_of_birth": groom[17],
            "age": groom[18],
            "profession": groom[19],
            "package": groom[20],
            "education": groom[21],
            "likes": groom[22],
            "dislikes": groom[23],
        }

        return render_template("groom-complete-profile.html", profile=groom_profile, bride=profile_data)
    else:
        flash("Groom profile not found!")
        return redirect(url_for("home"))


@app.route('/bride_complete_profile/<username>/<viewer>')
def bride_complete_profile(username, viewer):
    conn = sqlite3.connect("jeevansathi.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM groom_profile WHERE username = ?", (viewer,))
    profile = cursor.fetchone()

    if profile:
        # Map bride profile details to a dictionary
        profile_data = {
            "full_name": profile[1],
            "email_id": profile[2],
            "phone_number": profile[3],
            "country": profile[4],
            "state": profile[5],
            "city": profile[6],
            "address": profile[7],
            "diet": profile[8],
            "complexion": profile[9],
            "height": profile[10],
            "weight": profile[11],
            "image": profile[12].split(",")[0].replace("\\", "/"),  # Normalize path to use forward slashes
            "username": profile[14],
            "manglik": profile[16],
            "date_of_birth": profile[17],
            "age": profile[18],
            "profession": profile[19],
            "package": profile[20],
            "education": profile[21],
            "likes": profile[22],
            "dislikes": profile[23],
        }

    # Use 'username' and 'viewer' as needed
    conn = sqlite3.connect("jeevansathi.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Bride_profile WHERE username = ?", (username,))
    bride = cursor.fetchone()
    conn.close()

    if bride:
        # Map bride profile details to a dictionary
        bride_profile = {
            "full_name": bride[1],
            "email_id": bride[2],
            "phone_number": bride[3],
            "country": bride[4],
            "state": bride[5],
            "city": bride[6],
            "address": bride[7],
            "diet": bride[8],
            "complexion": bride[9],
            "height": bride[10],
            "weight": bride[11],
            "images": [url_for('uploaded_file', filename=img.replace("\\", "/")) for img in bride[12].split(",") if img],
            "video": bride[13].replace("\\", "/") if bride[13] else None,
            "username": bride[14],
            "manglik": bride[16],
            "date_of_birth": bride[17],
            "age": bride[18],
            "profession": bride[19],
            "package": bride[20],
            "education": bride[21],
            "likes": bride[22],
            "dislikes": bride[23],
        }

        return render_template("bride-complete-profile.html", profile=bride_profile, groom=profile_data)
    else:
        flash("Bride profile not found!")
        return redirect(url_for("home"))

# -------------------- Requests (Send/Approve/Cancel/Delete) --------------------
@app.route('/send_request', methods=['POST'])
def send_request():
    data = request.get_json()
    sender = data.get('sender')
    receiver = data.get('receiver')

    if not sender or not receiver:
        return jsonify({'error': 'Invalid data'}), 400

    # Connect to the SQLite database
    conn = sqlite3.connect('jeevansathi.db')
    cursor = conn.cursor()

    # Ensure the Requests table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            status_sender TEXT NOT NULL
        )
    ''')

    # Insert the request into the Requests table
    cursor.execute('''
        INSERT INTO Requests (sender, receiver, status_sender)
        VALUES (?, ?, ?)
    ''', (sender, receiver, 'Waiting'))

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

    # Emit real-time event to notify clients of the update
    socketio.emit('update_request', {'sender': sender, 'receiver': receiver}, to=None)

    return jsonify({'message': 'Request sent successfully'}), 200


@app.route('/approve_request', methods=['POST'])
def approve_request():
    data = request.get_json()
    sender = data.get('sender')
    receiver = data.get('receiver')

    conn = sqlite3.connect('jeevansathi.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE Requests
        SET status_sender = 'Approved'
        WHERE sender = ? AND receiver = ?
    ''', (sender, receiver))
    conn.commit()
    conn.close()

    # Emit real-time event to notify clients of the update
    socketio.emit('update_request', {'sender': sender, 'receiver': receiver}, to=None)

    return jsonify({'message': 'Request approved successfully'}), 200

@app.route('/cancel_request', methods=['POST'])
def cancel_request():
    data = request.get_json()
    sender = data.get('sender')
    receiver = data.get('receiver')

    conn = sqlite3.connect('jeevansathi.db')
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM Requests
        WHERE sender = ? AND receiver = ?
    ''', (sender, receiver))
    conn.commit()
    conn.close()

    # Emit real-time event to notify clients of the update
    socketio.emit('update_request', {'sender': sender, 'receiver': receiver}, to=None)

    return jsonify({'message': 'Request canceled successfully'}), 200

@app.route('/delete_request', methods=['POST'])
def delete_request():
    data = request.get_json()
    sender = data.get('sender')
    receiver = data.get('receiver')

    conn = sqlite3.connect('jeevansathi.db')
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM Requests
        WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
    ''', (sender, receiver, receiver, sender))
    conn.commit()
    conn.close()

    # Emit real-time event to notify clients of the update
    socketio.emit('update_request', {'sender': sender, 'receiver': receiver}, to=None)

    return jsonify({'message': 'Request deleted successfully'}), 200

@app.route('/save_message', methods=['POST'])
def save_message():
    data = request.get_json()
    sender = data.get('Sender')
    receiver = data.get('Receiver')
    message = data.get('Message')
    room_id = data.get('Room_ID')

    if not sender or not receiver or not message or not room_id:
        return jsonify({'error': 'Invalid data'}), 400

    # Get the current date and time
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%H:%M:%S')

    # Connect to the SQLite database
    conn = sqlite3.connect('jeevansathi.db')
    cursor = conn.cursor()

    # Ensure the Messages table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            message TEXT NOT NULL,
            room_id TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
    ''')

    # Insert the message into the Messages table
    cursor.execute('''
        INSERT INTO Messages (sender, receiver, message, room_id, date, time)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (sender, receiver, message, room_id, current_date, current_time))

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()

    return jsonify({'message': 'Message saved successfully'}), 200

@app.route('/get_messages', methods=['GET'])
def get_messages():
    room_id = request.args.get('room_id')
    sender = request.args.get('sender')
    receiver = request.args.get('receiver')

    if not room_id or not sender or not receiver:
        return jsonify({'error': 'Room ID, sender, and receiver are required'}), 400

    # Connect to the SQLite database
    conn = sqlite3.connect('jeevansathi.db')
    cursor = conn.cursor()

    # Fetch messages where sender and receiver match the given criteria
    cursor.execute('''
        SELECT sender, receiver, message, room_id, date, time
        FROM Messages
        WHERE room_id = ?
        AND ((sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?))
        ORDER BY date ASC, time ASC
    ''', (room_id, sender, receiver, receiver, sender))
    messages = cursor.fetchall()
    conn.close()

    # Map messages to a list of dictionaries
    messages_data = [
        {
            'sender': msg[0],
            'receiver': msg[1],
            'message': msg[2],
            'room_id': msg[3],
            'date': msg[4],
            'time': msg[5],
        }
        for msg in messages
    ]

    return jsonify(messages_data), 200

@app.route('/logout')
def logout():
    session.clear()  # Clear the session to log out the user
    flash("You have been logged out successfully!")
    return redirect(url_for('home'))

# -------------------- Chatbot (FAQs + Query) --------------------
# Load FAQs (safe fallback)
def get_db_connection():
    conn = sqlite3.connect('jeevansathi.db')
    conn.row_factory = sqlite3.Row
    return conn

# Load FAQs
with open('faqs.json', 'r') as f:
    faqs = json.load(f)

@app.route("/chatbot")
def hchatbot():
    return render_template("chatbot.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = (request.json.get("message") or "").strip().lower()
    if not user_msg:
        return jsonify({"reply": "Please enter a message."})

    # 1️⃣ Check FAQs first
    for item in faqs:
        if user_msg == (item.get("question") or "").strip().lower():
            return jsonify({"reply": item.get("answer", "Sorry, no answer found.")})

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row  # ✅ Important for dict-style access
    cursor = conn.cursor()

    # 2️⃣ Bride/Groom query patterns
    bride_pattern = re.search(r'brides?.*from ([\w\s]+).*age (\d+)(?: to (\d+))?', user_msg)
    groom_pattern = re.search(r'grooms?.*from ([\w\s]+).*age (\d+)(?: to (\d+))?', user_msg)

    if bride_pattern:
        city = " ".join([w.capitalize() for w in bride_pattern.group(1).split()])
        age_min = int(bride_pattern.group(2))
        age_max = int(bride_pattern.group(3)) if bride_pattern.group(3) else age_min

        if age_min == age_max:
            cursor.execute("""
                SELECT full_name, age, city, profession, education
                FROM Bride_profile
                WHERE city=? AND age=?
            """, (city, age_min))
        else:
            cursor.execute("""
                SELECT full_name, age, city, profession, education
                FROM Bride_profile
                WHERE city=? AND age BETWEEN ? AND ?
            """, (city, age_min, age_max))

        results = cursor.fetchall()
        conn.close()  # ✅ Close connection

        if results:
            reply = "\n".join([f"{b['full_name']}, Age: {b['age']}, City: {b['city']}, Profession: {b['profession']}, Education: {b['education']}" for b in results])
            return jsonify({"reply": reply})
        else:
            return jsonify({"reply": "No brides found matching your criteria."})

    elif groom_pattern:
        city = " ".join([w.capitalize() for w in groom_pattern.group(1).split()])
        age_min = int(groom_pattern.group(2))
        age_max = int(groom_pattern.group(3)) if groom_pattern.group(3) else age_min

        if age_min == age_max:
            cursor.execute("""
                SELECT full_name, age, city, profession, education
                FROM Groom_profile
                WHERE city=? AND age=?
            """, (city, age_min))
        else:
            cursor.execute("""
                SELECT full_name, age, city, profession, education
                FROM Groom_profile
                WHERE city=? AND age BETWEEN ? AND ?
            """, (city, age_min, age_max))

        results = cursor.fetchall()
        conn.close()

        if results:
            reply = "\n".join([f"{g['full_name']}, Age: {g['age']}, City: {g['city']}, Profession: {g['profession']}, Education: {g['education']}" for g in results])
            return jsonify({"reply": reply})
        else:
            return jsonify({"reply": "No grooms found matching your criteria."})

    # 3️⃣ Default fallback
    conn.close()
    return jsonify({"reply": "Sorry, I couldn't understand your query."})

    
# -------------------- Kundli Milan --------------------

@app.route("/kundli")
def kundli_home():
    # If you kept Kundli Milan's index.html under templates/kundli/index.html:
    return render_template("kundli.html")

@app.route("/kundli/match", methods=["POST"])
def kundli_match():
    if not groq_client:
        return jsonify({"error": "GROQ_API_KEY not configured"}), 500

    data = request.get_json() or {}
    groom = data.get("groom") or {}
    bride = data.get("bride") or {}

    prompt = f"""
Act as a professional Indian Vedic astrologer with expertise in Kundali Milan using the Ashta Koota system. 
Provide a detailed Kundali Milan report with an assumed Guna Milan score out of 36.

Details:
Groom:
- Name: {groom.get('name')}
- Date of Birth: {groom.get('dob')}
- Time of Birth: {groom.get('time')}
- Place of Birth: {groom.get('place')}

Bride:
- Name: {bride.get('name')}
- Date of Birth: {bride.get('dob')}
- Time of Birth: {bride.get('time')}
- Place of Birth: {bride.get('place')}

Output format:
1. 💖 Guna Milan Score: XX / 36
2. ❤️ Love Compatibility
3. 🏥 Health Alignment
4. 🏠 Family Life Outlook
5. 🌌 Planetary Influence
6. ☠️ Doshas Found and Remedies
7. 🧘 Advice for Relationship Harmony
"""

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a Kundli matching expert."},
                {"role": "user", "content": prompt}
            ]
        )
        result = resp.choices[0].message.content
        m = re.search(r"(\d{1,2})\s*/\s*36", result or "")
        score = m.group(1) if m else "N/A"
        return jsonify({"full_report": result, "score": score})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------- Run App --------------------
if __name__ == "__main__":
    import eventlet
    eventlet.monkey_patch()
    from app import app, socketio
    socketio.run(app, host="0.0.0.0", port=5050, debug=False)



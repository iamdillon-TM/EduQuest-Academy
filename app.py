# app.py
"""
EduQuest Academy - Flask application (single-file)
Ready for Render deployment using: gunicorn app:app
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---------------------------
# Basic logging
# ---------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eduquest")

# ---------------------------
# Flask app + config
# ---------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")

# Secret key: use env var in production. Fallback for local dev only.
app.secret_key = os.environ.get("EDUQUEST_SECRET_KEY") or os.urandom(24)

# Debug mode controlled by env var (set FLASK_DEBUG=1 to enable)
app.config['DEBUG'] = bool(int(os.environ.get("FLASK_DEBUG", "0")))

# ---------------------------
# Email configuration (ENV)
# ---------------------------
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "")

# ---------------------------
# Simulated data stores (replace with DB in production)
# ---------------------------
# Pre-hashed sample passwords (you can regenerate)
SAMPLE_PASSWORDS = {
    "admin_pw": generate_password_hash("8803"),
    "teacher_pw": generate_password_hash("1234"),
    "bob_pw": generate_password_hash("1234"),
    "alice_pw": generate_password_hash("5678"),
}

TEACHERS = {
    "Dillon": {
        "password": SAMPLE_PASSWORDS["admin_pw"],
        "full_name": "Dillon (Admin)",
        "role": "admin",
        "email": "dillon@eduquest.com",
        "status": "Senior Instructor",
        "id": "T001"
    },
    "Sarah": {
        "password": SAMPLE_PASSWORDS["teacher_pw"],
        "full_name": "Sarah Teacher",
        "role": "teacher",
        "email": "sarah@eduquest.com",
        "status": "Instructor",
        "id": "T002"
    }
}

STUDENTS = {
    "S101": {
        "id": "S101",
        "username": "Bob",
        "password": SAMPLE_PASSWORDS["bob_pw"],
        "name": "Bob Nguyễn",
        "course": "Let's Begin",
        "progress": "40%",
        "next_class": "2025-10-18 19:00",
        "assigned_teacher": "Dillon"
    },
    "S102": {
        "id": "S102",
        "username": "Alice",
        "password": SAMPLE_PASSWORDS["alice_pw"],
        "name": "Alice Tran",
        "course": "Intermediate Phase",
        "progress": "75%",
        "next_class": "2025-10-20 17:00",
        "assigned_teacher": "Sarah"
    }
}

COURSE_DETAILS = {
    "Let's Begin (Foundation Phase)": {
        "description": "Foundation course for absolute beginners.",
        "modules": ["Module 1", "Module 2", "Module 3"]
    },
    "Intermediate Phase (B1)": {
        "description": "Intermediate course",
        "modules": ["Module 6", "Module 7", "Module 8"]
    }
}

# ---------------------------
# Helper utilities
# ---------------------------

def get_student_by_username(username):
    """Return student dict by username or None."""
    for s in STUDENTS.values():
        if s.get("username") and s["username"].lower() == username.lower():
            return s
    return None

def send_registration_email(form_data: dict) -> bool:
    """
    Send registration lead email to RECIPIENT_EMAIL using SMTP.
    If SENDER_EMAIL or SENDER_PASSWORD or RECIPIENT_EMAIL are not configured,
    this function will log and return True as a simulated send.
    """
    if not (SENDER_EMAIL and SENDER_PASSWORD and RECIPIENT_EMAIL):
        logger.warning("Email env vars not configured. Simulating registration email send.")
        logger.info("Registration form data: %s", form_data)
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = "NEW COURSE REGISTRATION - EduQuest Website"

        body = (
            f"New registration lead:\n\n"
            f"Full name: {form_data.get('full_name')}\n"
            f"Email: {form_data.get('email')}\n"
            f"Phone: {form_data.get('phone')}\n"
            f"Student age: {form_data.get('student_age')}\n"
            f"Current level: {form_data.get('current_level')}\n"
            f"Preferred course: {form_data.get('preferred_course')}\n"
            f"Notes: {form_data.get('notes')}\n"
        )
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
        server.ehlo()
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        logger.info("Registration email sent successfully to %s", RECIPIENT_EMAIL)
        return True
    except Exception as exc:
        logger.exception("Failed to send registration email: %s", exc)
        return False

# ---------------------------
# Routes: Public + Pages
# ---------------------------

@app.route("/")
def home():
    """Home page (hero + nav)."""
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Public registration form."""
    if request.method == "POST":
        form_data = request.form.to_dict()
        logger.info("Received registration form: %s", form_data)
        ok = send_registration_email(form_data)
        session['registration_name'] = form_data.get("full_name", "Valued Student")
        # We still show success page even if email simulated/failed, with a warning in server logs.
        return redirect(url_for("registration_success"))
    return render_template("registration.html")

@app.route("/registration_success")
def registration_success():
    name = session.pop("registration_name", "Valued Student")
    return render_template("registration_success.html", name=name)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/courses")
def courses():
    # pass course details
    return render_template("courses.html", course_details=COURSE_DETAILS)

@app.route("/foundation_phase")
def foundation_phase():
    return render_template("foundation_phase.html")

@app.route("/intermediate_phase")
def intermediate_phase():
    return render_template("intermediate_phase.html")

@app.route("/advance_phase")
def advance_phase():
    return render_template("advance_phase.html")

@app.route("/terms_and_conditions")
def terms_and_conditions():
    return render_template("terms_and_conditions.html")

# ---------------------------
# Authentication: Student & Teacher
# ---------------------------

@app.route("/teacher_login", methods=["GET", "POST"])
def teacher_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        teacher = TEACHERS.get(username)
        if teacher and check_password_hash(teacher["password"], password):
            session.clear()
            session["logged_in"] = True
            session["user_type"] = "teacher"
            session["username"] = username
            session["role"] = teacher.get("role", "teacher")
            logger.info("Teacher logged in: %s", username)
            return redirect(url_for("unified_teacher_dashboard"))
        else:
            return render_template("teacher_login.html", error="Invalid username or password.")
    return render_template("teacher_login.html")

@app.route("/student_login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        student = get_student_by_username(username)
        if student and check_password_hash(student["password"], password):
            session.clear()
            session["logged_in"] = True
            session["user_type"] = "student"
            session["username"] = student["username"]
            session["student_id"] = student["id"]
            logger.info("Student logged in: %s (id=%s)", student["username"], student["id"])
            return redirect(url_for("student_dashboard"))
        else:
            return render_template("student_login.html", error="Invalid student username or password.")
    return render_template("student_login.html")

# ---------------------------
# Dashboards
# ---------------------------

@app.route("/teacher_dashboard")
def unified_teacher_dashboard():
    if session.get("user_type") != "teacher":
        return redirect(url_for("teacher_login"))

    username = session.get("username")
    teacher = TEACHERS.get(username)
    if not teacher:
        session.clear()
        return redirect(url_for("teacher_login"))

    is_admin = teacher.get("role") == "admin"
    # find assigned students
    assigned = [s for s in STUDENTS.values() if s.get("assigned_teacher") == username]

    context = {
        "name": teacher.get("full_name"),
        "email": teacher.get("email"),
        "status": teacher.get("status"),
        "assigned_students": assigned,
        "is_admin": is_admin,
        "all_students": list(STUDENTS.values()) if is_admin else None,
        "all_teachers": list(TEACHERS.keys()) if is_admin else None
    }
    return render_template("teacher_dashboard.html", teacher=context)

@app.route("/student_dashboard")
def student_dashboard():
    if session.get("user_type") != "student":
        return redirect(url_for("student_login"))

    username = session.get("username")
    student = get_student_by_username(username)
    if not student:
        session.clear()
        return redirect(url_for("student_login"))

    # Compose student view
    student_view = {
        "username": student["username"],
        "full_name": student["name"],
        "email": f"{student['username'].lower()}@eduquest.com",
        "current_package": student["course"],
        "teacher": student["assigned_teacher"],
        "course_progress": {"total_lessons": 20, "lessons_completed": 8, "lessons_remaining": 12, "next_topic": "Unit 10: ..."},
        "upcoming_classes": [
            {"date": "2025-10-18", "time": "19:00 - 20:00", "topic": "Unit 9", "teacher": student["assigned_teacher"]}
        ]
    }
    return render_template("student_dashboard.html", student=student_view)

# ---------------------------
# Student profile & course pages
# ---------------------------
@app.route("/my_course")
def my_course():
    if session.get("user_type") != "student":
        return redirect(url_for("student_login"))
    username = session.get("username")
    student = get_student_by_username(username)
    if not student:
        session.clear()
        return redirect(url_for("student_login"))

    course_name = student.get("course")
    course_info = COURSE_DETAILS.get(course_name, {"description": "No info", "modules": []})
    return render_template("my_course.html", student=student, course_info=course_info)

@app.route("/student_profile")
def student_profile():
    if session.get("user_type") != "student":
        return redirect(url_for("student_login"))
    student = get_student_by_username(session.get("username"))
    if not student:
        session.clear()
        return redirect(url_for("student_login"))
    return render_template("student_profile.html", student=student)

@app.route("/submit_profile", methods=["POST"])
def submit_profile():
    if session.get("user_type") != "student":
        return redirect(url_for("student_login"))
    full_name = request.form.get("full_name")
    learning_goals = request.form.get("learning_goals")
    experience_level = request.form.get("experience_level")
    # Simulate save...
    logger.info("Profile submitted: %s | %s | %s", full_name, learning_goals, experience_level)
    return render_template("profile_confirmation.html", name=full_name, goals=learning_goals, experience=experience_level)

# ---------------------------
# Payments & invoice helpers
# ---------------------------
def get_invoice(student_username, invoice_id):
    # Simulate invoice lookup
    # For demo, return a fake invoice if invoice_id matches a pattern
    student = get_student_by_username(student_username)
    if not student:
        return None
    invoices = [
        {"id": "INV-9021", "date": "2025-09-01", "amount": 2500000, "status": "Paid"},
        {"id": "INV-9022", "date": "2025-10-15", "amount": 3200000, "status": "Unpaid"}
    ]
    inv = next((i for i in invoices if i["id"] == invoice_id), None)
    return student, inv

@app.route("/payments")
def payments():
    if session.get("user_type") != "student":
        return redirect(url_for("student_login"))
    student = get_student_by_username(session.get("username"))
    # supply sample invoices
    invoices = [
        {"id": "INV-9021", "date": "2025-09-01", "amount": 2500000, "status": "Paid"},
        {"id": "INV-9022", "date": "2025-10-15", "amount": 3200000, "status": "Unpaid"}
    ]
    return render_template("invoices.html", student=student, invoices=invoices)

@app.route("/vietqr_details/<invoice_id>")
def vietqr_details(invoice_id):
    if session.get("user_type") != "student":
        return redirect(url_for("student_login"))
    student, inv = get_invoice(session.get("username"), invoice_id)
    if not inv:
        return redirect(url_for("payments"))
    return render_template("vietqr_details.html", student=student, invoice=inv)

@app.route("/international_details/<invoice_id>")
def international_details(invoice_id):
    if session.get("user_type") != "student":
        return redirect(url_for("student_login"))
    student, inv = get_invoice(session.get("username"), invoice_id)
    if not inv:
        return redirect(url_for("payments"))
    return render_template("international_details.html", student=student, invoice=inv)

# ---------------------------
# Admin endpoints (example permission checks)
# ---------------------------
@app.route("/admin/update_assignment", methods=["POST"])
def admin_update_assignment():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Permission denied"}), 403
    # Implement update logic here...
    return jsonify({"success": True, "message": "Assignment updated"})

@app.route("/admin/update_lesson", methods=["POST"])
def admin_update_lesson():
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Permission denied"}), 403
    return jsonify({"success": True, "message": "Lesson updated"})

# ---------------------------
# Chat API (simple / local)
# ---------------------------
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json() or {}
    message = (data.get("message") or "").lower()

    # Basic canned responses and routing
    if "course" in message or "level" in message:
        reply = "We offer Let's Phonics, Let's Begin, Let's Go, and Side by Side. Tell me the learner's age and level and I'll recommend one."
    elif "register" in message or "sign up" in message:
        reply = "You can register via the Register page. Which course are you interested in?"
    elif "price" in message or "cost" in message:
        reply = "Pricing depends on the package — visit Payments or ask me to compare packages."
    elif "schedule" in message or "class" in message:
        if session.get("user_type") == "student":
            student = get_student_by_username(session.get("username"))
            if student:
                reply = f"Next class: {student.get('next_class')} with {student.get('assigned_teacher')}."
            else:
                reply = "I can't find your schedule — please check your dashboard."
        else:
            reply = "I can show schedules if you log in as a student."
    elif "hello" in message or "hi" in message:
        reply = "Hello! I'm EduBot. I can help with courses, registration, or payments."
    else:
        reply = "Sorry, I'm still learning. Try asking about courses, registration, or your schedule."

    return jsonify({"response": reply})

# ---------------------------
# Logout
# ---------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ---------------------------
# Health / debug endpoint (optional)
# ---------------------------
@app.route("/_status")
def status():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})

# ---------------------------
# Run (local dev). Render will use gunicorn, not this block.
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting EduQuest app on 0.0.0.0:%s (debug=%s)", port, app.config["DEBUG"])
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])

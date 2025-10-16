"""
EduQuest Academy - Flask application (single-file)
Ready for Render deployment using: gunicorn app:app
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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

# Secret key from environment
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

# Debug mode (safe handling of different env values)
flask_debug = os.environ.get("FLASK_DEBUG", "0").lower()
if flask_debug in ["1", "true", "debug"]:
    app.config['DEBUG'] = True
else:
    app.config['DEBUG'] = False

# ---------------------------
# Email configuration from ENV
# ---------------------------
SENDER_EMAIL = os.environ.get("EMAIL_HOST_USER", "")
SENDER_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", SENDER_EMAIL)  # fallback

# ---------------------------
# Simulated data stores (replace with DB in production)
# ---------------------------
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

# --- UPDATED STUDENTS DATA with invoices for new routes ---
STUDENTS = {
    "S101": {
        "id": "S101",
        "username": "Bob",
        "password": SAMPLE_PASSWORDS["bob_pw"],
        "name": "Bob Nguyễn",
        "course": "Let's Begin",
        "progress": "40%",
        "next_class": "2025-10-18 19:00",
        "assigned_teacher": "Dillon",
        "invoices": [
            {"id": "INV-20251001", "date": "2025-10-01", "amount": 4000000, "status": "Paid"},
            {"id": "INV-20251101", "date": "2025-11-01", "amount": 4000000, "status": "Unpaid"}
        ]
    },
    "S102": {
        "id": "S102",
        "username": "Alice",
        "password": SAMPLE_PASSWORDS["alice_pw"],
        "name": "Alice Tran",
        "course": "Intermediate Phase",
        "progress": "75%",
        "next_class": "2025-10-20 17:00",
        "assigned_teacher": "Sarah",
        "invoices": [
            {"id": "INV-20250915", "date": "2025-09-15", "amount": 4800000, "status": "Paid"},
            {"id": "INV-20251015", "date": "2025-10-15", "amount": 4800000, "status": "Unpaid"}
        ]
    }
}
# ---------------------------------------------------------

COURSE_DETAILS = {
    "Let's Begin (Foundation Phase)": {
        "description": "Foundation course for absolute beginners. Focuses on core grammar, basic vocabulary, and simple conversation structures.",
        "modules": ["Module 1: Greetings & Introductions", "Module 2: Daily Routines", "Module 3: Telling Time", "Module 4: Simple Past Tense", "Module 5: Future Plans"]
    },
    "Intermediate Phase (B1)": {
        "description": "Intermediate course focusing on fluency, complex grammar, and practical application in real-world scenarios. Essential for B1 certification.",
        "modules": ["Module 6: Conditional Statements", "Module 7: Narrative Tenses", "Module 8: Expressing Opinions", "Module 9: Reading Comprehension", "Module 10: Debate Skills"]
    }
}

# Mock progress data used for student-facing pages
STUDENT_MOCK_PROGRESS = {"total_lessons": 20, "lessons_completed": 8, "lessons_remaining": 12, "next_topic": "Unit 10: Presenting Your Ideas"}

# ---------------------------
# Helper utilities
# ---------------------------
def get_student_by_username(username):
    for s in STUDENTS.values():
        if s.get("username") and s["username"].lower() == username.lower():
            return s
    return None

def get_full_course_key(short_name):
    # Attempts to find the full key in COURSE_DETAILS based on the short name stored in student data
    for key in COURSE_DETAILS:
        if short_name in key:
            return key
    return None

def get_invoice_by_id(student_id, invoice_id):
    student = next((s for s in STUDENTS.values() if s["id"] == student_id), None)
    if student:
        return next((i for i in student.get("invoices", []) if i["id"] == invoice_id), None)
    return None

def send_registration_email(form_data: dict) -> bool:
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
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        form_data = request.form.to_dict()
        logger.info("Received registration form: %s", form_data)
        send_registration_email(form_data)
        session['registration_name'] = form_data.get("full_name", "Valued Student")
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
# Authentication
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
            logger.info("Student logged in: %s", student["username"])
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

    student = get_student_by_username(session.get("username"))
    if not student:
        session.clear()
        return redirect(url_for("student_login"))

    # Use the mock progress data for consistency across student pages
    student_view = {
        "username": student["username"],
        "full_name": student["name"],
        "email": f"{student['username'].lower()}@eduquest.com",
        "current_package": student["course"],
        "teacher": student["assigned_teacher"],
        "course_progress": STUDENT_MOCK_PROGRESS, # Use the shared mock data
        "upcoming_classes": [
            {"date": student["next_class"].split(" ")[0], "time": "19:00 - 20:00", "topic": "Unit 9", "teacher": student["assigned_teacher"]}
        ]
    }
    return render_template("student_dashboard.html", student=student_view)

# ---------------------------
# Student Portal Routes (New)
# ---------------------------

@app.route("/my_course")
def my_course():
    if session.get("user_type") != "student":
        return redirect(url_for("student_login"))

    student = get_student_by_username(session.get("username"))
    if not student:
        session.clear()
        return redirect(url_for("student_login"))

    course_name = student["course"]
    full_course_key = get_full_course_key(course_name)

    course_info = COURSE_DETAILS.get(full_course_key, {
        "description": "Course details not found. Please contact support.", 
        "modules": ["N/A"]
    })
    
    # Pass student with course progress data for the template
    student_for_template = {
        "course_progress": STUDENT_MOCK_PROGRESS,
    }
    
    return render_template(
        "my_course.html", 
        course_name=course_name,
        course_info=course_info,
        student=student_for_template
    )

@app.route("/invoices")
def invoices():
    if session.get("user_type") != "student":
        return redirect(url_for("student_login"))

    student = get_student_by_username(session.get("username"))
    if not student:
        session.clear()
        return redirect(url_for("student_login"))

    student_view = {
        "full_name": student["name"],
        "invoices": student.get("invoices", [])
    }
    
    return render_template("invoices.html", student=student_view)

@app.route("/payment_options/<invoice_id>")
def payment_options(invoice_id):
    if session.get("user_type") != "student":
        return redirect(url_for("student_login"))
        
    student = get_student_by_username(session.get("username"))
    if not student:
        session.clear()
        return redirect(url_for("student_login"))
        
    invoice = get_invoice_by_id(student["id"], invoice_id)
    if not invoice:
        return f"Invoice {invoice_id} not found.", 404
    
    return render_template(
        "payments.html", 
        invoice=invoice # Passed to allow the template to build the international_details link
    )

@app.route("/international_details/<invoice_id>")
def international_details(invoice_id):
    if session.get("user_type") != "student":
        return redirect(url_for("student_login"))
        
    student = get_student_by_username(session.get("username"))
    if not student:
        session.clear()
        return redirect(url_for("student_login"))
        
    invoice = get_invoice_by_id(student["id"], invoice_id)
    if not invoice:
        return f"Invoice {invoice_id} not found.", 404

    student_view = {"username": student["username"]}
    
    return render_template(
        "international_details.html", 
        invoice=invoice,
        student=student_view
    )


# ---------------------------
# Logout
# ---------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ---------------------------
# Health / debug endpoint
# ---------------------------
@app.route("/_status")
def status():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})

# ---------------------------
# API for chatbot
# ---------------------------
@app.route("/api/chat", methods=["POST"])
def chatbot_api():
    data = request.get_json()
    message = data.get("message", "").lower()
    logger.info("Chatbot received: %s", message)

    # Example: simple keyword responses
    if "schedule" in message:
        response = "Your next class is on Friday at 19:00."
    elif "payment" in message:
        response = "You can complete payments via the 'Payments' button on the homepage."
    elif "level" in message:
        response = "Please take our placement test to determine your course level."
    elif "let's go" in message or "lets go" in message:
        response = "Let's Go is our Foundation Phase interactive course for beginners."
    else:
        response = "I'm here to help! Could you please rephrase your question or choose one of the quick queries?"

    return jsonify({"response": response})

# ---------------------------
# Run (only for local dev)
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
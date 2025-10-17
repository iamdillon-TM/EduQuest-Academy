"""
EduQuest Academy - Flask application (single-file)
Ready for Render deployment using: gunicorn app:app
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
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
# Flask automatically finds the 'templates' folder and the 'static' folder.
app = Flask(__name__, static_folder="static")

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
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", "recipient@example.com")
# SMTP details
SMTP_SERVER = "smtp.gmail.com"  # Assuming Gmail or similar
SMTP_PORT = 587

# ---------------------------
# DUMMY DATABASE/DATA STRUCTURE 
# ---------------------------
USERS = {
    # Dummy user for testing login
    "teststudent": generate_password_hash("password123"),
    # Dummy teacher
    "testteacher": generate_password_hash("teacher456"),
    # Admin User for Bypass
    "Dillon": generate_password_hash("supersecretadminpassword"),
}

INVOICES = {
    1001: {"id": 1001, "date": "2025-09-01", "amount": 12000000, "status": "Paid"},
    1002: {"id": 1002, "date": "2025-10-01", "amount": 10800000, "status": "Unpaid"},
    1003: {"id": 1003, "date": "2025-11-01", "amount": 10800000, "status": "Unpaid"},
}

STUDENT_DATA = {
    "username": "teststudent",
    "full_name": "Alex Johnson",
    "course_name": "Intermediate Phase: Skill Builder",
    "invoices": list(INVOICES.values()),
    "course_progress": {
        "lessons_completed": 12,
        "total_lessons": 40,
        "lessons_remaining": 28,
        "next_topic": "Writing Persuasive Essays (Lesson 13)",
    },
    "course_info": {
        "description": "Designed for students transitioning from beginner to conversational English. Develops core grammar, conversational fluency, and elementary writing skills.",
        "modules": [
            "Module 1: Advanced Tenses",
            "Module 2: Opinion & Debate",
            "Module 3: Formal Letter Writing",
            "Module 4: Persuasive Essay Structure",
            "Module 5: Media Analysis",
            "Module 6: Final Project Presentation",
        ]
    }
}

TEACHER_DATA = {
    "username": "testteacher",
    "name": "Ms. Evelyn Reed",
    "status": "Online",
    "email": "evelyn.r@eduquest.academy",
    "assigned_students": [
        {"name": "Nguyen Van A", "course": "Foundation 2", "progress": "50%", "next_class": "Thu 17:00"},
        {"name": "Tran Thi B", "course": "Intermediate 1", "progress": "75%", "next_class": "Fri 19:00"},
    ],
    "upcoming_schedule": [
        {"date": "Oct 17 (Thu)", "time": "17:00", "topic": "Simple Past Tense Review", "student": "Nguyen Van A"},
        {"date": "Oct 18 (Fri)", "time": "19:00", "topic": "Debate Skills: Environment", "student": "Tran Thi B"},
    ]
}

# ---------------------------
# Helper Functions
# ---------------------------

def send_email(subject, body, recipient):
    """Sends an email notification."""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logger.warning("Email credentials not set. Skipping email.")
        return False
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
        server.quit()
        logger.info(f"Email successfully sent to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False 

def get_user_data(username):
    """Retrieves user data based on role."""
    if username == "teststudent":
        return STUDENT_DATA
    if username == "testteacher":
        return TEACHER_DATA
    return None

# ---------------------------
# Routes
# ---------------------------

@app.route("/")
@app.route("/home")
def home():
    # Renders: home.html
    return render_template("home.html")

# FIX 1: Added the missing /contact route
@app.route("/contact")
def contact():
    # Renders: contact.html
    return render_template("contact.html")

@app.route("/courses")
def courses():
    # Renders: courses.html
    return render_template("courses.html")

@app.route("/foundation")
def foundation_phase():
    # Renders: foundation_phase.html
    return render_template("foundation_phase.html")

@app.route("/intermediate")
def intermediate_phase():
    # Renders: intermediate_phase.html
    return render_template("intermediate_phase.html")

@app.route("/advance")
def advance_phase():
    # Renders: advance_phase.html
    return render_template("advance_phase.html")

@app.route("/terms-and-conditions")
def terms_and_conditions():
    # Renders: terms_and_conditions.html
    return render_template("terms_and_conditions.html")

# --- Login/Auth Routes ---
@app.route("/login", methods=["GET", "POST"])
def login():
    # Generic login redirects to student login
    return redirect(url_for('student_login'))

# Student-specific login 
@app.route("/student-login", methods=["GET", "POST"])
def student_login():
    # Renders: student_login.html
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        # Admin Bypass (Dillon)
        if username == "Dillon" and check_password_hash(USERS.get(username, ""), password):
            session["logged_in"] = True
            session["username"] = username
            session["role"] = "Admin"
            return redirect(url_for("teacher_dashboard"))

        # Regular Student Login
        if username in USERS and check_password_hash(USERS[username], password) and "student" in username:
            session["logged_in"] = True
            session["username"] = username
            session["role"] = "Student"
            return redirect(url_for("student_dashboard"))
        else:
            return render_template("student_login.html", error="Invalid Student ID or Password.")
    
    return render_template("student_login.html")

# Teacher-specific login 
@app.route("/teacher-login", methods=["GET", "POST"])
def teacher_login():
    # Renders: teacher_login.html
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Admin Bypass (Dillon)
        if username == "Dillon" and check_password_hash(USERS.get(username, ""), password):
            session["logged_in"] = True
            session["username"] = username
            session["role"] = "Admin"
            return redirect(url_for("teacher_dashboard"))

        # Regular Teacher Login
        if username in USERS and check_password_hash(USERS[username], password) and "teacher" in username:
            session["logged_in"] = True
            session["username"] = username
            session["role"] = "Teacher"
            return redirect(url_for("teacher_dashboard"))
        else:
            return render_template("teacher_login.html", error="Invalid Teacher Username or Password.")
    
    return render_template("teacher_login.html")


# --- Registration Routes ---
@app.route("/registration", methods=["GET", "POST"])
def registration():
    # Renders: registration.html
    if request.method == "POST":
        data = request.form
        
        # 1. Send internal notification email
        subject = f"New Course Registration from {data.get('parent_name', 'N/A')}"
        body = (
            f"Registration Details:\n"
            f"Parent: {data.get('parent_name', 'N/A')} ({data.get('parent_email', 'N/A')})\n"
            f"Student: {data.get('student_name', 'N/A')} (Age: {data.get('student_age', 'N/A')})\n"
            f"Course: {data.get('course_phase', 'N/A')} ({data.get('course_level', 'N/A')})\n"
            f"Format: {data.get('class_format', 'N/A')}\n"
            f"Timezone: {data.get('timezone', 'N/A')}\n"
            f"Notes: {data.get('notes', 'N/A')}\n"
        )
        send_email(subject, body, RECIPIENT_EMAIL)
        
        # 2. Redirect to a thank you page
        return redirect(url_for("registration_success")) 

    return render_template("registration.html")

@app.route("/registration-success")
def registration_success():
    """Renders the success page after registration."""
    # Renders: registration_success.html
    return render_template("registration_success.html")


# --- Dashboard Routes (Requires Login) ---

# Student Dashboard
@app.route("/student-dashboard")
def student_dashboard():
    # Renders: student_dashboard.html
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session.get('username')
    student = get_user_data(username)
    
    # Check if user is a student or the admin
    if not student or ("student" not in username and session.get('role') != 'Admin'):
        session.clear()
        return redirect(url_for('login'))

    return render_template("student_dashboard.html", student=student)

# Student Profile
@app.route("/student-profile")
def student_profile():
    # Renders: student_profile.html
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session.get('username')
    student = get_user_data(username)
    
    if not student or ("student" not in username and session.get('role') != 'Admin'):
        session.clear()
        return redirect(url_for('login'))

    return render_template("student_profile.html", student=student)


# Teacher Dashboard
@app.route("/teacher-dashboard")
def teacher_dashboard():
    # Renders: teacher_dashboard.html
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session.get('username')
    teacher = get_user_data(username)

    # Check if user is a teacher or the admin (Dillon)
    if not teacher and session.get('role') != 'Admin':
        session.clear()
        return redirect(url_for('login'))
        
    # If the user is the admin, customize the teacher data for display purposes
    if session.get('role') == 'Admin':
        # Create a mutable copy of TEACHER_DATA to modify for the admin view
        admin_view_data = TEACHER_DATA.copy() 
        admin_view_data['name'] = "Admin Dillon"
        admin_view_data['status'] = "Superuser"
        admin_view_data['email'] = "dillon@eduquest.academy"
        teacher = admin_view_data

    return render_template("teacher_dashboard.html", teacher=teacher)


@app.route("/my-course")
def my_course():
    # Renders: my_course.html
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session.get('username')
    student = get_user_data(username)
    
    if not student or ("student" not in username and session.get('role') != 'Admin'):
        session.clear()
        return redirect(url_for('login'))

    return render_template(
        "my_course.html", 
        student=student, 
        course_name=student["course_name"],
        course_info=student["course_info"]
    )

@app.route("/invoices")
def invoices():
    # Renders: invoices.html
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session.get('username')
    student = get_user_data(username)
    
    if not student or ("student" not in username and session.get('role') != 'Admin'):
        session.clear()
        return redirect(url_for('login'))

    return render_template("invoices.html", student=student)

# FIX 2: Added a simple redirect to support templates linking to 'payments' 
# which should really point to 'invoices'. This solves the BuildError in the logs.
@app.route("/payments")
def payments():
    """Redirects the endpoint used by home.html to the working invoices page."""
    return redirect(url_for('invoices'))

# --- Payment Routes ---
@app.route("/payments/<int:invoice_id>")
def payment_options(invoice_id):
    # Renders: payments.html
    invoice = INVOICES.get(invoice_id)
    
    if not invoice:
        abort(404, description="Invoice not found.") 
        
    return render_template("payments.html", invoice=invoice)

@app.route("/international/<int:invoice_id>")
def international_details(invoice_id):
    # Renders: international_details.html
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    username = session.get('username')
    student = get_user_data(username)
    
    if not student:
        return redirect(url_for('login')) 
    
    invoice = INVOICES.get(invoice_id)
    
    if not invoice:
        abort(404, description="Invoice not found.")

    return render_template(
        "international_details.html", 
        invoice=invoice, 
        student=student
    )

@app.route("/vietqr/<int:invoice_id>")
def vietqr_details(invoice_id):
    # Renders: vietqr_details.html
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    username = session.get('username')
    student = get_user_data(username)
    
    if not student:
        return redirect(url_for('login')) 
    
    invoice = INVOICES.get(invoice_id)
    
    if not invoice:
        abort(404, description="Invoice not found.")

    return render_template(
        "vietqr_details.html", 
        invoice=invoice, 
        student=student
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
        response = "Your next class is on **Friday at 19:00**."
    elif "payment" in message:
        response = "You can complete payments via the **'Payments'** button on the homepage, or view invoices on your **Dashboard**."
    elif "level" in message:
        response = "Please take our **placement test** to determine your course level."
    elif "let's go" in message or "lets go" in message:
        response = "**Let's Go** is our Foundation Phase interactive course for beginners (Ages 6-10)."
    else:
        response = "I'm here to help! Could you please rephrase your question or choose one of the quick queries (schedule, payment, level, Let's Go)?"

    return jsonify({"response": response})

# ---------------------------
# Run (only for local development)
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
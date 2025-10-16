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
# Flask app + config (CRITICAL CHANGE HERE)
# ---------------------------
# The fix: Set template_folder to '.' (current directory) 
# because HTML files are placed in the root, not a 'templates' folder.
app = Flask(__name__, static_folder="static", template_folder=".")

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

def get_student_data():
    """Retrieves student data from the session."""
    username = session.get('username')
    if username == "teststudent":
        return STUDENT_DATA
    return None

# ---------------------------
# Routes
# ---------------------------

@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/courses")
def courses():
    return render_template("courses.html")

@app.route("/foundation")
def foundation_phase():
    return render_template("foundation_phase.html")

@app.route("/intermediate")
def intermediate_phase():
    return render_template("intermediate_phase.html")

@app.route("/advance")
def advance_phase():
    return render_template("advance_phase.html")

@app.route("/contact")
def contact():
    return "Contact Page Coming Soon!"


# --- Login/Auth Routes ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in USERS and check_password_hash(USERS[username], password):
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("student_dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password.")
    
    return render_template("login.html")


# --- Registration Routes ---
@app.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        data = request.form
        
        # 1. Send internal notification email
        subject = f"New Course Registration from {data['parent_name']}"
        body = (
            f"Registration Details:\n"
            f"Parent: {data['parent_name']} ({data['parent_email']})\n"
            f"Student: {data['student_name']} (Age: {data['student_age']})\n"
            f"Course: {data['course_phase']} ({data['course_level']})\n"
            f"Format: {data['class_format']}\n"
            f"Timezone: {data['timezone']}\n"
            f"Notes: {data['notes']}\n"
        )
        send_email(subject, body, RECIPIENT_EMAIL)
        
        # 2. Redirect to a thank you page
        return redirect(url_for("home")) 

    return render_template("registration.html")


# --- Dashboard Routes (Requires Login) ---
@app.route("/dashboard")
def student_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    student = get_student_data()
    if not student:
        session.clear()
        return redirect(url_for('login'))

    return render_template("student_dashboard.html", student=student)

@app.route("/my-course")
def my_course():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    student = get_student_data()
    if not student:
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
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    student = get_student_data()
    if not student:
        session.clear()
        return redirect(url_for('login'))

    return render_template("invoices.html", student=student)


# --- Payment Routes ---
@app.route("/payments/<int:invoice_id>")
def payment_options(invoice_id):
    invoice = INVOICES.get(invoice_id)
    
    if not invoice:
        abort(404, description="Invoice not found.") 
        
    return render_template("payments.html", invoice=invoice)

@app.route("/international/<int:invoice_id>")
def international_details(invoice_id):
    student = get_student_data()
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
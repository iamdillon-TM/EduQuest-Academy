import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash 

app = Flask(__name__)

# =========================================================
# === CRITICAL: SECURITY & ENVIRONMENT CONFIGURATION ===
# =========================================================
# 1. SECRET KEY: MUST be set via an environment variable in production.
#    If the environment variable SECRET_KEY isn't set, it uses a random key for development.
#    NEVER use a fixed, hardcoded string for app.secret_key in a public file.
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# 2. DEBUG MODE: Set to False for production environments.
#    Flask defaults to False if not specified, but this is explicit.
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG') == '1' or False

# =========================================================
# === CONFIGURATION: LOGIN & EMAIL SETTINGS ===
# =========================================================
# I've generated and used secure hashes for the initial passwords.
ADMIN_PASSWORD_HASHED = generate_password_hash("8803") 
TEACHER_PASSWORD_HASHED = generate_password_hash("1234")
BOB_PASSWORD_HASHED = generate_password_hash("1234")
ALICE_PASSWORD_HASHED = generate_password_hash("5678")
JOHN_PASSWORD_HASHED = generate_password_hash("0000")

# Placeholder settings for email simulation
SENDER_EMAIL = "your_sending_email@gmail.com"        
RECIPIENT_EMAIL = "trung.thanh.dillon@gmail.com"  

# =========================================================
# === DATA SOURCES (SIMULATED) ===
# =========================================================

# 1. Teachers/Admins Data Store 
TEACHERS = {
    "Dillon": {
        "password": ADMIN_PASSWORD_HASHED, 
        "full_name": "Dillon Teacher (Admin)", 
        "role": "admin", 
        "email": "dillon@eduquest.com",
        "status": "Senior Instructor"
    },
    "Teacher": {
        "password": TEACHER_PASSWORD_HASHED, 
        "full_name": "Sarah Teacher", 
        "role": "teacher", 
        "email": "sarah@eduquest.com",
        "status": "Junior Instructor"
    }
}

# 2. Student Data Store
STUDENTS = {
    'S101': {
        'id': 'S101', 
        'username': 'Bob', 
        'password': BOB_PASSWORD_HASHED, # Hashed
        'name': 'Bob Nguyễn', 
        'course': "Let's Go", 
        'progress': '40%', 
        'next_class': 'Oct 18 (19:00)', 
        'assigned_teacher_id': 'Dillon'
    },
    'S102': {
        'id': 'S102', 
        'username': 'Alice', 
        'password': ALICE_PASSWORD_HASHED, # Hashed
        'name': 'Alice Tran', 
        'course': 'Side by Side', 
        'progress': '75%', 
        'next_class': 'Oct 20 (17:00)', 
        'assigned_teacher_id': 'Dillon'
    },
    'S103': {
        'id': 'S103', 
        'username': 'John', 
        'password': JOHN_PASSWORD_HASHED, # Hashed
        'name': 'John Doe', 
        'course': 'Let\'s Begin', 
        'progress': '10%', 
        'next_class': 'Oct 22 (18:00)', 
        'assigned_teacher_id': 'Teacher'
    }
}

# 3. Lesson Plans/Work (kept as is)
LESSON_WORK = {
    'S101': [
        {'date': '2025-10-18', 'topic': 'Unit 9: Simple Past', 'plan': 'Focus on regular vs irregular verbs. Homework: Page 45.', 'uploaded_work': 'Completed worksheet 1'},
    ],
    'S103': [
        {'date': '2025-10-22', 'topic': 'Colours and Numbers', 'plan': 'Game-based learning. Homework: Draw a colorful monster.', 'uploaded_work': None},
    ]
}

# 4. Mock Student Data Retrieval
def get_student_data(username):
    """Fetches comprehensive student data based on username for dashboard pages."""
    # Find the corresponding student entry
    student_entry = next((s for s in STUDENTS.values() if s['username'] == username), None)
    
    if student_entry:
        # A real application would fetch this full detail from a database linked to the student_entry ID
        # For simulation, we return the 'Bob' data structure if the user is a known student.
        return {
            'username': student_entry['username'], 
            'full_name': student_entry['name'], 
            'email': f"{student_entry['username'].lower()}@eduquest.com", 
            'current_package': student_entry['course'], 
            'teacher': student_entry['assigned_teacher_id'],
            # The remaining data is mocked for a complete dashboard view
            'course_progress': {'total_lessons': 20, 'lessons_completed': 8, 'lessons_remaining': 12, 'next_topic': 'Unit 10: Comparative Adjectives'},
            'upcoming_classes': [
                {'date': '2025-10-18', 'time': '19:00 - 20:00 (VN time)', 'topic': 'Unit 9: Simple Past', 'teacher': 'Dillon'},
                {'date': '2025-10-21', 'time': '20:00 - 21:00 (VN time)', 'topic': 'Unit 10: Comparative Adjectives', 'teacher': 'Dillon'},
            ],
            'role': 'student',
            'learning_goals': 'Improve speaking fluency.', 
            'experience_level': 'Elementary',
            'invoices': [
                {'id': 'INV-9021', 'date': '2025-09-01', 'amount': 2500000, 'status': 'Paid'},
                {'id': 'INV-9022', 'date': '2025-10-15', 'amount': 3200000, 'status': 'Unpaid'}
            ]
        }
    return None

# =========================================================
# === EMAIL FUNCTION (SIMULATED) ===
# =========================================================
def send_registration_email(form_data):
    """Simulates sending registration form details to admin."""
    print(f"--- SIMULATING EMAIL SEND to {RECIPIENT_EMAIL} ---")
    return True 


# =========================================================
# === CORE ROUTES (LOGIN/LOGOUT/DASHBOARD) ===
# =========================================================
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        form_data = request.form
        if send_registration_email(form_data):
            session['registration_name'] = form_data.get('full_name', 'Customer')
            return redirect(url_for('registration_success'))
        else:
            # Handle potential email failure gracefully
            return render_template('registration.html', error="Failed to send registration email. Please try again.")
    return render_template('registration.html')

@app.route('/registration_success')
def registration_success():
    name = session.pop('registration_name', 'Valued Customer')
    return render_template('registration_success.html', name=name)

@app.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        teacher_data = TEACHERS.get(username)

        # Security check: use check_password_hash
        if teacher_data and check_password_hash(teacher_data['password'], password):
            session.update({'logged_in': True, 'user_type': 'teacher', 'username': username, 'role': teacher_data['role']})
            return redirect(url_for('unified_teacher_dashboard'))
        return render_template('teacher_login.html', error="Invalid username or password.")
    return render_template('teacher_login.html')

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Find student data by username
        student_data = next((s for s in STUDENTS.values() if s['username'] == username), None)

        # Security check: use check_password_hash
        if student_data and check_password_hash(student_data['password'], password):
            session.update({'logged_in': True, 'user_type': 'student', 'username': username, 'role': 'student'})
            return redirect(url_for('student_dashboard')) 

        return render_template('student_login.html', error="Invalid student username or password.")
    return render_template('student_login.html')

@app.route('/teacher_dashboard')
def unified_teacher_dashboard():
    # Require teacher login
    if session.get('user_type') != 'teacher':
        return redirect(url_for('teacher_login'))
    
    teacher_id = session.get('username')
    teacher_info = TEACHERS.get(teacher_id)
    # Check if teacher_info exists before accessing keys
    if not teacher_info:
        session.clear()
        return redirect(url_for('teacher_login'))

    is_admin = teacher_info['role'] == 'admin'

    assigned_students = [
        student_data for student_data in STUDENTS.values() 
        if student_data['assigned_teacher_id'] == teacher_id
    ]

    teacher_data = {
        'name': teacher_info['full_name'], 'email': teacher_info['email'],
        'status': teacher_info['status'], 'role': teacher_info['role'],
        'is_admin': is_admin, 'assigned_students': assigned_students,
        'upcoming_schedule': [] 
    }

    if is_admin:
        # Show all students for Admin Roster
        teacher_data['all_students'] = [{'id': sid, 'name': s['name'], 'course': s['course'], 'teacher_id': s['assigned_teacher_id']} for sid, s in STUDENTS.items()]
        teacher_data['all_teachers'] = TEACHERS.keys()

    return render_template('teacher_dashboard.html', teacher=teacher_data)

@app.route('/student_dashboard')
def student_dashboard():
    # Require student login
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    
    student_data = get_student_data(session.get('username'))
    if not student_data:
        # Handle case where session username exists but data lookup fails
        session.clear() 
        return redirect(url_for('student_login'))
        
    return render_template('student_dashboard.html', student=student_data)

# =========================================================
# === DEDICATED TEMPLATE ROUTES (PAYMENTS & PUBLIC PAGES) ===
# =========================================================

# --- Payments Workflow (Requires Student Login) ---

def get_invoice_details(username, invoice_id):
    """Helper function to safely retrieve invoice details."""
    student_data = get_student_data(username)
    if not student_data:
        return None, None

    invoice = next((inv for inv in student_data.get('invoices', []) if inv['id'] == invoice_id), None)
    return student_data, invoice

@app.route('/payments')
def payments():
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    student_data = get_student_data(session.get('username'))
    return render_template('invoices.html', student=student_data)

@app.route('/payment_options/<invoice_id>')
def payment_options(invoice_id):
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))

    student_data, invoice = get_invoice_details(session.get('username'), invoice_id)
    if not invoice:
        return redirect(url_for('payments')) 

    return render_template('payment_options.html', student=student_data, invoice=invoice)

@app.route('/vietqr_details/<invoice_id>')
def vietqr_details(invoice_id):
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
        
    student_data, invoice = get_invoice_details(session.get('username'), invoice_id)
    if not invoice:
        return redirect(url_for('payments')) 

    return render_template('vietqr_details.html', student=student_data, invoice=invoice)

@app.route('/international_details/<invoice_id>')
def international_details(invoice_id):
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
        
    student_data, invoice = get_invoice_details(session.get('username'), invoice_id)
    if not invoice:
        return redirect(url_for('payments')) 

    return render_template('international_details.html', student=student_data, invoice=invoice)

# --- Public Course Pages (NO Student Data Passed) ---

@app.route('/courses')
def courses():
    return render_template('courses.html')

@app.route('/foundation_phase')
def foundation_phase():
    return render_template('foundation_phase.html')

@app.route('/intermediate_phase')
def intermediate_phase():
    return render_template('intermediate_phase.html')
    
@app.route('/advance_phase')
def advance_phase():
    return render_template('advance_phase.html')

# --- Other Student & Utility Pages ---

@app.route('/my_course')
def my_course():
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    student_data = get_student_data(session.get('username'))
    if not student_data: # Error check
        session.clear() 
        return redirect(url_for('student_login'))
    return render_template('my_course.html', student=student_data)

@app.route('/student_profile')
def student_profile():
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    student_data = get_student_data(session.get('username'))
    if not student_data: # Error check
        session.clear()
        return redirect(url_for('student_login'))
    return render_template('student_profile.html', student=student_data)

@app.route('/terms_and_conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')

# =========================================================
# === ADMIN API ROUTES (Permission Checks) ===
# =========================================================
@app.route('/admin/update_assignment', methods=['POST'])
def update_assignment():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Permission denied: Only Admin can make changes.'}), 403
    
    # Logic to update student assignment (omitted for brevity)
    return jsonify({'success': True, 'message': f'Student assignment successfully updated.'})

@app.route('/admin/update_lesson', methods=['POST'])
def update_lesson():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Permission denied: Only Admin can make changes.'}), 403

    # Logic to update lesson plan (omitted for brevity)
    return jsonify({'success': True, 'message': f'Lesson plan successfully updated.'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# =========================================================
# === RUN APP ===
# =========================================================
if __name__ == '__main__':
    # Use app.config['DEBUG'] which is set based on environment variable FLASK_DEBUG
    print("🚀 Starting EduQuest Academy web app locally...")
    app.run(debug=app.config['DEBUG'])
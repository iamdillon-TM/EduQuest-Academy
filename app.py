from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)
# IMPORTANT: Change this key before deployment!
app.secret_key = 'your_very_secret_key_here' 

# =========================================================
# === CONFIGURATION: LOGIN & EMAIL SETTINGS ===
# =========================================================
ADMIN_PASSWORD = "8803" 
# Placeholder settings for email simulation
SENDER_EMAIL = "your_sending_email@gmail.com"      
RECIPIENT_EMAIL = "trung.thanh.dillon@gmail.com"  

# =========================================================
# === DATA SOURCES (SIMULATED) ===
# =========================================================

# 1. Teachers/Admins Data Store 
TEACHERS = {
    "Dillon": {
        "password": ADMIN_PASSWORD, 
        "full_name": "Dillon Teacher (Admin)", 
        "role": "admin", 
        "email": "dillon@eduquest.com",
        "status": "Senior Instructor"
    },
    "Teacher": {
        "password": "1234", 
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
        'name': 'Bob Nguyễn', 
        'course': "Let's Go", 
        'progress': '40%', 
        'next_class': 'Oct 18 (19:00)', 
        'assigned_teacher_id': 'Dillon'
    },
    'S102': {
        'id': 'S102', 
        'username': 'Alice', 
        'name': 'Alice Tran', 
        'course': 'Side by Side', 
        'progress': '75%', 
        'next_class': 'Oct 20 (17:00)', 
        'assigned_teacher_id': 'Dillon'
    },
    'S103': {
        'id': 'S103', 
        'username': 'John', 
        'name': 'John Doe', 
        'course': 'Let\'s Begin', 
        'progress': '10%', 
        'next_class': 'Oct 22 (18:00)', 
        'assigned_teacher_id': 'Teacher'
    }
}

# 3. Lesson Plans/Work
LESSON_WORK = {
    'S101': [
        {'date': '2025-10-18', 'topic': 'Unit 9: Simple Past', 'plan': 'Focus on regular vs irregular verbs. Homework: Page 45.', 'uploaded_work': 'Completed worksheet 1'},
    ],
    'S103': [
        {'date': '2025-10-22', 'topic': 'Colours and Numbers', 'plan': 'Game-based learning. Homework: Draw a colorful monster.', 'uploaded_work': None},
    ]
}

# 4. Mock Student Data Retrieval (for student dashboard)
def get_student_data(username="Bob"):
    """Fetches student data based on username."""
    # This data is passed to all student dashboard pages (payments, my_course, profile)
    if username == "Bob":
        return {
            'username': 'Bob', 'full_name': 'Bob Nguyễn', 'email': 'bob.nguyen@email.com', 
            'current_package': "Let's Go (Level 3)", 'teacher': 'Dillon',
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
                {'id': 'INV-9022', 'date': '2025-10-15', 'amount': 3200000, 'status': 'Unpaid'} # The one Bob needs to pay
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
            return render_template('registration.html', error="Email failed.")
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

        if teacher_data and teacher_data['password'] == password:
            session.update({'logged_in': True, 'user_type': 'teacher', 'username': username, 'role': teacher_data['role']})
            return redirect(url_for('unified_teacher_dashboard'))
        return render_template('teacher_login.html', error="Invalid username or password.")
    return render_template('teacher_login.html')

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        is_bob = (username == "Bob" and password == "1234")
        
        if is_bob:
            session.update({'logged_in': True, 'user_type': 'student', 'username': username, 'role': 'student'})
            return redirect(url_for('student_dashboard')) 

        return render_template('student_login.html', error="Invalid student ID or password.")
    return render_template('student_login.html')

@app.route('/teacher_dashboard')
def unified_teacher_dashboard():
    if session.get('user_type') != 'teacher':
        return redirect(url_for('teacher_login'))
    
    teacher_id = session.get('username')
    teacher_info = TEACHERS.get(teacher_id)
    is_admin = teacher_info['role'] == 'admin'

    assigned_students = [
        student_data for student_data in STUDENTS.values() 
        if student_data['assigned_teacher_id'] == teacher_id
    ]

    teacher_data = {
        'name': teacher_info['full_name'], 'email': teacher_info['email'],
        'status': teacher_info['status'], 'role': teacher_info['role'],
        'is_admin': is_admin, 'assigned_students': assigned_students,
        'upcoming_schedule': [] # Placeholder for simplicity
    }

    if is_admin:
        # Simplified student details for Admin Roster
        teacher_data['all_students'] = [{'id': sid, 'name': s['name'], 'course': s['course'], 'teacher_id': s['assigned_teacher_id']} for sid, s in STUDENTS.items()]
        teacher_data['all_teachers'] = TEACHERS.keys()

    return render_template('teacher_dashboard.html', teacher=teacher_data)

@app.route('/student_dashboard')
def student_dashboard():
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    
    student_data = get_student_data(session.get('username'))
    if not student_data:
        return redirect(url_for('student_login'))
        
    return render_template('student_dashboard.html', student=student_data)

# =========================================================
# === DEDICATED TEMPLATE ROUTES (INCLUDING PAYMENTS) ===
# =========================================================

# --- Payments Workflow (Requires Student Login) ---

@app.route('/payments')
def payments():
    """Renders the student's invoice history (invoices.html). This is the main /payments page."""
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
        
    student_data = get_student_data(session.get('username'))
    return render_template('invoices.html', student=student_data)

@app.route('/payment_options/<invoice_id>')
def payment_options(invoice_id):
    """Renders the payment method options (payment_options.html)."""
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))

    student_data = get_student_data(session.get('username'))
    invoice = next((inv for inv in student_data.get('invoices', []) if inv['id'] == invoice_id), None)

    if not invoice:
        return redirect(url_for('payments')) 

    return render_template('payment_options.html', student=student_data, invoice=invoice)

@app.route('/vietqr_details/<invoice_id>')
def vietqr_details(invoice_id):
    """Renders the vietqr_details.html template."""
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
        
    student_data = get_student_data(session.get('username'))
    invoice = next((inv for inv in student_data.get('invoices', []) if inv['id'] == invoice_id), None)

    if not invoice:
        return redirect(url_for('payments')) 

    return render_template('vietqr_details.html', student=student_data, invoice=invoice)

@app.route('/international_details/<invoice_id>')
def international_details(invoice_id):
    """Renders the international_details.html template."""
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
        
    student_data = get_student_data(session.get('username'))
    invoice = next((inv for inv in student_data.get('invoices', []) if inv['id'] == invoice_id), None)

    if not invoice:
        return redirect(url_for('payments')) 

    return render_template('international_details.html', student=student_data, invoice=invoice)


# --- Public Course Pages (NO Student Data Passed) ---

@app.route('/courses')
def courses():
    """Renders the main courses list page."""
    return render_template('courses.html')

@app.route('/foundation_phase')
def foundation_phase():
    """Renders the foundation_phase.html template."""
    # NO student data is passed here (public page)
    return render_template('foundation_phase.html')

@app.route('/intermediate_phase')
def intermediate_phase():
    """Renders the intermediate_phase.html template."""
    # NO student data is passed here (public page)
    return render_template('intermediate_phase.html')
    
@app.route('/advance_phase')
def advance_phase():
    """Renders the advance_phase.html template."""
    # NO student data is passed here (public page)
    return render_template('advance_phase.html')


# --- Other Student & Utility Pages ---

@app.route('/my_course')
def my_course():
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    student_data = get_student_data(session.get('username'))
    return render_template('my_course.html', student=student_data)

@app.route('/student_profile')
def student_profile():
    if session.get('user_type') != 'student':
        return redirect(url_for('student_login'))
    student_data = get_student_data(session.get('username'))
    return render_template('student_profile.html', student=student_data)


@app.route('/terms_and_conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')


# =========================================================
# === ADMIN API ROUTES ===
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
    print("🚀 Starting EduQuest Academy web app...")
    app.run(debug=True)
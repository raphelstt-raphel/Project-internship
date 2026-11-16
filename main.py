# app.py (main application)
import os
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = 'studytracker'

mysql = MySQL(app)

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# Database initialization (run once)
def init_db():
    with app.app_context():
        conn = mysql.connection
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create subjects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Create topics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS topics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                subject_id INT NOT NULL,
                name VARCHAR(255) NOT NULL,
                is_completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
            )
        ''')
        
        # Create schedule table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                subject_id INT NOT NULL,
                topic_id INT,
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                is_completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()

# Send email function
def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Schedule email notifications
def schedule_emails():
    with app.app_context():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get all upcoming schedules in the next 24 hours
        tomorrow = datetime.now() + timedelta(days=1)
        cursor.execute('''
            SELECT s.*, u.email, sub.name as subject_name, t.name as topic_name
            FROM schedule s
            JOIN users u ON s.user_id = u.id
            JOIN subjects sub ON s.subject_id = sub.id
            LEFT JOIN topics t ON s.topic_id = t.id
            WHERE s.start_time BETWEEN %s AND %s AND s.is_completed = FALSE
        ''', (datetime.now(), tomorrow))
        
        schedules = cursor.fetchall()
        
        for schedule in schedules:
            # Format email content
            subject = "Upcoming Study Session Reminder"
            body = f"""
            <h2>Study Session Reminder</h2>
            <p>You have a study session scheduled:</p>
            <p><strong>Subject:</strong> {schedule['subject_name']}</p>
            <p><strong>Topic:</strong> {schedule['topic_name'] or 'General revision'}</p>
            <p><strong>Time:</strong> {schedule['start_time'].strftime('%Y-%m-%d %H:%M')} to {schedule['end_time'].strftime('%H:%M')}</p>
            <p>Please be prepared for your study session.</p>
            <br>
            <p>Best regards,<br>Study Tracker Team</p>
            """
            
            # Send email
            send_email(schedule['email'], subject, body)

# Schedule the email job to run every hour
scheduler.add_job(schedule_emails, 'interval', hours=1)

# Routes
@app.route('/')
def index():
    if 'loggedin' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login/', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()
        
        if user:
            session['loggedin'] = True
            session['userid'] = user['id']
            session['email'] = user['email']
            message = 'Welcome to Study Tracker!'
            flash(message, 'success')
            return redirect(url_for('dashboard'))
        else:
            message = 'Please enter correct email/password!'
            flash(message, 'error')
    
    return render_template('login.html', message=message)

@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        
        if account:
            message = 'Account already exists!'
            flash(message, 'error')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
            flash(message, 'error')
        elif not email or not password:
            message = 'Please fill out the form!'
            flash(message, 'error')
        else:
            cursor.execute('INSERT INTO users (email, password) VALUES (%s, %s)', (email, password))
            mysql.connection.commit()
            message = 'You have successfully registered!'
            flash(message, 'success')
            return redirect(url_for('login'))
    
    return render_template('signup.html', message=message)

@app.route('/dashboard/')
def dashboard():
    if 'loggedin' in session:
        user_id = session['userid']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Get user's subjects
        cursor.execute('SELECT * FROM subjects WHERE user_id = %s', (user_id,))
        subjects = cursor.fetchall()
        
        # Get user's topics with progress
        subject_progress = {}
        for subject in subjects:
            cursor.execute('''
                SELECT COUNT(*) as total, 
                       SUM(CASE WHEN is_completed THEN 1 ELSE 0 END) as completed 
                FROM topics WHERE subject_id = %s
            ''', (subject['id'],))
            progress = cursor.fetchone()
            subject_progress[subject['id']] = {
                'total': progress['total'] or 0,
                'completed': progress['completed'] or 0,
                'percentage': round((progress['completed'] or 0) / (progress['total'] or 1) * 100) if progress['total'] else 0
            }
        
        # Get upcoming schedule
        cursor.execute('''
            SELECT s.*, sub.name as subject_name, t.name as topic_name
            FROM schedule s
            JOIN subjects sub ON s.subject_id = sub.id
            LEFT JOIN topics t ON s.topic_id = t.id
            WHERE s.user_id = %s AND s.start_time >= %s
            ORDER BY s.start_time ASC
            LIMIT 5
        ''', (user_id, datetime.now()))
        
        upcoming_schedule = cursor.fetchall()
        
        return render_template('dashboard.html', 
                              email=session['email'], 
                              subjects=subjects, 
                              subject_progress=subject_progress,
                              upcoming_schedule=upcoming_schedule)
    
    return redirect(url_for('login'))

@app.route('/logout/')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route('/subjects/', methods=['GET', 'POST'])
def subjects():
    if 'loggedin' in session:
        user_id = session['userid']
        
        if request.method == 'POST':
            subject_name = request.form['subject_name']
            
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Check if user already has 7 subjects
            cursor.execute('SELECT COUNT(*) as count FROM subjects WHERE user_id = %s', (user_id,))
            count = cursor.fetchone()['count']
            
            if count >= 7:
                flash('Maximum 7 subjects allowed!', 'error')
                return redirect(url_for('subjects'))
            
            # Add new subject
            cursor.execute('INSERT INTO subjects (user_id, name) VALUES (%s, %s)', (user_id, subject_name))
            mysql.connection.commit()
            flash('Subject added successfully!', 'success')
            return redirect(url_for('subjects'))
        
        # GET request - show subjects
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM subjects WHERE user_id = %s', (user_id,))
        subjects = cursor.fetchall()
        
        return render_template('subjects.html', subjects=subjects, max_subjects=7)
    
    return redirect(url_for('login'))

@app.route('/topics/<int:subject_id>', methods=['GET', 'POST'])
def topics(subject_id):
    if 'loggedin' in session:
        user_id = session['userid']
        
        # Verify subject belongs to user
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM subjects WHERE id = %s AND user_id = %s', (subject_id, user_id))
        subject = cursor.fetchone()
        
        if not subject:
            flash('Subject not found!', 'error')
            return redirect(url_for('subjects'))
        
        if request.method == 'POST':
            topic_name = request.form['topic_name']
            
            # Add new topic
            cursor.execute('INSERT INTO topics (subject_id, name) VALUES (%s, %s)', (subject_id, topic_name))
            mysql.connection.commit()
            flash('Topic added successfully!', 'success')
            return redirect(url_for('topics', subject_id=subject_id))
        
        # GET request - show topics
        cursor.execute('SELECT * FROM topics WHERE subject_id = %s', (subject_id,))
        topics = cursor.fetchall()
        
        return render_template('topics.html', subject=subject, topics=topics)
    
    return redirect(url_for('login'))

@app.route('/toggle_topic/<int:topic_id>')
def toggle_topic(topic_id):
    if 'loggedin' in session:
        user_id = session['userid']
        
        # Verify topic belongs to user
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT t.* FROM topics t
            JOIN subjects s ON t.subject_id = s.id
            WHERE t.id = %s AND s.user_id = %s
        ''', (topic_id, user_id))
        
        topic = cursor.fetchone()
        
        if not topic:
            flash('Topic not found!', 'error')
            return redirect(url_for('dashboard'))
        
        # Toggle completion status
        new_status = not topic['is_completed']
        cursor.execute('UPDATE topics SET is_completed = %s WHERE id = %s', (new_status, topic_id))
        mysql.connection.commit()
        
        flash(f'Topic marked as {"completed" if new_status else "incomplete"}!', 'success')
        return redirect(request.referrer or url_for('dashboard'))
    
    return redirect(url_for('login'))

@app.route('/schedule/', methods=['GET', 'POST'])
def study_schedule():
    if 'loggedin' in session:
        user_id = session['userid']
        
        if request.method == 'POST':
            start_time_str = request.form['start_time']
            end_time_str = request.form['end_time']
            study_hours = request.form['study_hours']
            
            # Parse times
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            study_hours_per_day = float(study_hours)
            
            # Get user's subjects and topics
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM subjects WHERE user_id = %s', (user_id,))
            subjects = cursor.fetchall()
            
            topics = []
            for subject in subjects:
                cursor.execute('SELECT * FROM topics WHERE subject_id = %s AND is_completed = FALSE', (subject['id'],))
                subject_topics = cursor.fetchall()
                for topic in subject_topics:
                    topics.append({
                        'id': topic['id'],
                        'name': topic['name'],
                        'subject_id': subject['id'],
                        'subject_name': subject['name']
                    })
            
            # Generate schedule (simplified algorithm)
            schedule = generate_schedule(
                user_id, 
                subjects, 
                topics, 
                start_time, 
                end_time, 
                study_hours_per_day
            )
            
            # Save schedule to database
            for item in schedule:
                cursor.execute('''
                    INSERT INTO schedule (user_id, subject_id, topic_id, start_time, end_time)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (user_id, item['subject_id'], item.get('topic_id'), item['start_time'], item['end_time']))
            
            mysql.connection.commit()
            
            # Send schedule via email
            email_body = format_schedule_email(schedule)
            send_email(session['email'], "Your Study Schedule", email_body)
            
            flash('Study schedule created and sent to your email!', 'success')
            return redirect(url_for('dashboard'))
        
        return render_template('schedule.html')
    
    return redirect(url_for('login'))

def generate_schedule(user_id, subjects, topics, start_time, end_time, study_hours_per_day):
    schedule = []
    current_date = datetime.now().date()
    
    # Calculate available time per day in minutes
    start_dt = datetime.combine(current_date, start_time)
    end_dt = datetime.combine(current_date, end_time)
    available_minutes_per_day = (end_dt - start_dt).total_seconds() / 60
    
    # Distribute study time across subjects (simplified)
    subject_ids = [s['id'] for s in subjects]
    subject_study_minutes = available_minutes_per_day / len(subject_ids)
    
    # Create a 7-day schedule
    for day in range(7):
        day_date = current_date + timedelta(days=day)
        day_start = datetime.combine(day_date, start_time)
        
        for i, subject_id in enumerate(subject_ids):
            start_dt = day_start + timedelta(minutes=i * subject_study_minutes)
            end_dt = start_dt + timedelta(minutes=subject_study_minutes)
            
            # Find a topic for this subject if available
            topic_id = None
            subject_topics = [t for t in topics if t['subject_id'] == subject_id]
            if subject_topics:
                topic = subject_topics[0]  # Simple round-robin
                topic_id = topic['id']
                # Remove this topic from the list so we don't schedule it again
                topics = [t for t in topics if t['id'] != topic_id]
            
            schedule.append({
                'subject_id': subject_id,
                'subject_name': next(s['name'] for s in subjects if s['id'] == subject_id),
                'topic_id': topic_id,
                'topic_name': next((t['name'] for t in subject_topics if t['id'] == topic_id), None),
                'start_time': start_dt,
                'end_time': end_dt
            })
    
    return schedule

def format_schedule_email(schedule):
    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; }
            .schedule-item { margin-bottom: 15px; padding: 10px; border-left: 4px solid #4CAF50; background-color: #f9f9f9; }
            .date { font-weight: bold; color: #333; margin-bottom: 5px; }
            .subject { font-weight: bold; color: #4CAF50; }
            .topic { color: #666; }
            .time { color: #888; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <h2>Your Study Schedule</h2>
        <p>Here is your personalized study schedule for the next week:</p>
    """
    
    current_date = None
    for item in schedule:
        item_date = item['start_time'].strftime('%Y-%m-%d')
        if item_date != current_date:
            if current_date is not None:
                html += "</div>"
            html += f"<h3>{item['start_time'].strftime('%A, %B %d, %Y')}</h3><div>"
            current_date = item_date
        
        html += f"""
        <div class="schedule-item">
            <div class="time">{item['start_time'].strftime('%H:%M')} - {item['end_time'].strftime('%H:%M')}</div>
            <div class="subject">{item['subject_name']}</div>
            <div class="topic">{item['topic_name'] or 'General revision'}</div>
        </div>
        """
    
    html += """
        </div>
        <br>
        <p>Good luck with your studies!</p>
        <p>Best regards,<br>Study Tracker Team</p>
    </body>
    </html>
    """
    
    return html

@app.route('/api/schedule')
def api_schedule():
    if 'loggedin' in session:
        user_id = session['userid']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            SELECT s.*, sub.name as subject_name, t.name as topic_name
            FROM schedule s
            JOIN subjects sub ON s.subject_id = sub.id
            LEFT JOIN topics t ON s.topic_id = t.id
            WHERE s.user_id = %s AND s.start_time >= %s
            ORDER BY s.start_time ASC
        ''', (user_id, datetime.now()))
        
        schedule = cursor.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        for item in schedule:
            item['start_time'] = item['start_time'].strftime('%Y-%m-%d %H:%M:%S')
            item['end_time'] = item['end_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify(schedule)
    
    return jsonify({'error': 'Not authenticated'}), 401

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

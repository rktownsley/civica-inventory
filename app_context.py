from flask import Flask, flash, render_template, request, redirect, url_for, session, jsonify, Response, send_file, abort, g
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

import sqlite3

import jwt
from urllib.parse import unquote
from jwt import ExpiredSignatureError, InvalidTokenError
import shutil

import csv
import io
from datetime import datetime, timedelta
import pytz
from collections import defaultdict

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from email.message import EmailMessage

import fcntl  # For file locking

# For feedback survey
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'inventorynotificationbot@gmail.com'
SMTP_PASSWORD = 'abvdmqdsasblfnda'
TO_EMAIL = "rktownsley@ucdavis.edu"


import json

import openpyxl
from openpyxl.utils import get_column_letter

import os
from werkzeug.utils import secure_filename

# Define allowed extensions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure random string in production


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = os.path.join(BASE_DIR, "user_databases")
os.makedirs(DB_FOLDER, exist_ok=True)


def apply_clinic_scope(conn, clinic_id):
    """
    Create TEMP views that transparently restrict all tables
    to the given clinic_id.
    """
    cursor = conn.cursor()

    # Defensive quoting (prevents SQL injection)
    clinic_id_sql = clinic_id.replace("'", "''")

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
          AND name NOT LIKE 'sqlite_%';
    """)

    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        # IMPORTANT: explicitly target TEMP schema
        cursor.execute(f"DROP VIEW IF EXISTS temp.{table}")

        # Create scoped TEMP view
        cursor.execute(f"""
            CREATE TEMP VIEW {table} AS
            SELECT *
            FROM main.{table}
            WHERE clinic_id = '{clinic_id_sql}'
        """)

    conn.commit()


def set_clinic_database():
    """Set the global DATABASE for the currently logged-in user."""
    global DATABASE, DB_CONN

    clinic = session.get("clinic")
    if not clinic:
        raise Exception("No logged-in clinic found in session.")

    safe_clinic = "".join(c for c in clinic if c.isalnum() or c in ("-", "_"))
    db_path = os.path.join(DB_FOLDER, "merged.db")

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Unified database not found: {db_path}")

    DATABASE = db_path

    DB_CONN = sqlite3.connect(DATABASE)
    DB_CONN.row_factory = sqlite3.Row

    # 🔒 Enforce row-level isolation
    apply_clinic_scope(DB_CONN, safe_clinic)

    clean_empty_values()

    print(
        f"THIS IS THE CURRENT DATABASE (PATH): {db_path} "
        f"(clinic='{safe_clinic}')"
    )


# Define where the uploaded photos are stored
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Get the absolute path of the project root directory
project_root = os.path.abspath(os.path.dirname(__file__))


MESSAGE_FILE = os.path.join(os.path.dirname(__file__), "messages.json")
FEEDBACK_FILE = os.path.join(app.root_path, "feedback.json")


import fcntl  # Add this import at the top

import time

# Add a lock file path
MESSAGE_LOCK_FILE = os.path.join(os.path.dirname(__file__), "messages.lock")

def load_messages():
    if os.path.exists(MESSAGE_FILE):
        with open(MESSAGE_FILE, "r") as f:
            return json.load(f)
    return []

def save_messages(messages):
    with open(MESSAGE_FILE, "w") as f:
        json.dump(messages, f)

def update_messages_safely(update_func):
    """
    Safely update messages with exclusive locking for the entire operation.
    update_func should be a function that takes the current messages list and modifies it.
    """
    # Create lock file if it doesn't exist
    lock_file = open(MESSAGE_LOCK_FILE, 'w')
    
    try:
        # Get exclusive lock (blocks until available)
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        
        # Load messages
        messages = load_messages()
        
        # Apply updates
        update_func(messages)
        
        # Save messages
        save_messages(messages)
        
    finally:
        # Release lock
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()


def normalize_date(date_str):
    if not date_str:
        return None

    # Replace all dashes with slashes
    date_str = date_str.replace('-', '/')

    parts = date_str.split('/')
    if len(parts) != 3:
        return None  # Invalid format

    month, day, year = parts

    # Pad month and day with zeros
    if len(month) == 1:
        month = '0' + month
    if len(day) == 1:
        day = '0' + day

    # Convert 2-digit year to 4-digit year
    if len(year) == 2:
        year = '20' + year
    elif len(year) != 4:
        return None

    return f'{month}/{day}/{year}'

# Utility to execute queries and return results as dictionaries
def query_db(query, args=(), one=False):
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row  # This makes SQLite return rows as dictionaries
        cur = conn.cursor()
        cur.execute(query, args)
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv


# Flask's before_request hook will run this function before each request
@app.before_request
def before_request():
    # Don't apply the check if we are already on the login page
    if request.endpoint in ['login', 'auth', 'signup', 'support', 'submit_feedback', 'download_all']:
        return  # Skip the redirect check if we're already on the login page

    # Check if the user is logged in and whether the DB is initialized
    if "clinic" not in session and not session.get("db_initialized", False):
        print("Clinic not in session or DB not initialized. Redirecting to login.")
        return redirect(url_for('login'))
    
    # If clinic is in session and DB is not initialized yet, initialize it
    if "clinic" in session and not session.get("db_initialized", False):
        init_db()  # Initialize DB for the user
        session["db_initialized"] = True  # Mark DB as initialized for the session

    else:
        print("Database already initialized.")


@app.before_request
def enforce_viewer_location():
    if request.endpoint == 'static':
        return
    
    if request.endpoint in ['login', 'auth', 'signup', 'support', 'submit_feedback', 'download_all']:
        return  # Skip the redirect check if we're already on the login page

    if (
        session.get('user') == 'klohc'
        and session.get('clinic') == 'inventory'
        and request.method == 'GET'
    ):
        location = request.args.get('location')

        if location != 'Knights Landing':
            args = request.args.to_dict(flat=True)
            args['location'] = 'Knights Landing'

            return redirect(url_for(request.endpoint, **args))
        
    elif (
        session.get('user') == 'tepati'
        and session.get('clinic') == 'inventory'
        and request.method == 'GET'
    ):
        location = request.args.get('location')

        if location != 'Tepati':
            args = request.args.to_dict(flat=True)
            args['location'] = 'Tepati'

            return redirect(url_for(request.endpoint, **args))
        

# Initialize database
def init_db():
    
    # This will set the correct clinic database based on the session
    set_clinic_database()

    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()


        # Fetch all rows with non-null expiration_date
        cur.execute("SELECT id, expiration_date FROM items WHERE expiration_date IS NOT NULL")
        rows = cur.fetchall()

        for item_id, raw_date in rows:
            normalized = normalize_date(raw_date)
            if normalized:
                cur.execute(
                    "UPDATE items SET expiration_date = ? WHERE id = ?",
                    (normalized, item_id)
                )


        # Check and add columns if they do not exist
        columns_to_add = [
            ("aka", "TEXT"),
            ("location1", "TEXT"),
            ("location2", "TEXT"),
            ("location3", "TEXT"),
            ("location4", "TEXT"),
            ("medication_class", "TEXT"),
        ]

        # Alter the table to add missing columns
        for column, column_type in columns_to_add:
            try:
                cur.execute(f"ALTER TABLE items ADD COLUMN {column} {column_type};")
            except sqlite3.OperationalError:
                # Column already exists
                pass

        cur.executescript('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                aka TEXT,
                status TEXT,
                quantity INTEGER NOT NULL,
                location TEXT,
                location1 TEXT,
                location2 TEXT,
                location3 TEXT,
                location4 TEXT,
                category TEXT,
                description TEXT,
                instrument_type TEXT,
                expiration_date TEXT,
                supplier TEXT,
                order_number TEXT,
                order_quantity INTEGER,
                dosage TEXT,
                form TEXT,
                lot_number TEXT,
                ndc TEXT,
                dispense_used INTEGER,
                dispense_as TEXT,
                unit_quantity INTEGER,
                prescription_type TEXT,
                medication_class TEXT,
                minimum_supply INTEGER, -- Added column for minimum supply before photo_url
                photo_url TEXT,          -- Added column for photo URL
                last_edit DATETIME,
                restock BOOLEAN DEFAULT 0,-- Added column to mark items as restock requested (0 = not requested, 1 = requested)
                removed BOOLEAN DEFAULT 0, -- Added column to mark items as removed (0 = not removed, 1 = removed)
                delisted BOOLEAN DEFAULT 0 -- Added column to mark items as delisted (0 = not delisted, 1 = delisted) NEW 10/24/25
            );
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS locs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                value TEXT NOT NULL,
                site TEXT NOT NULL
            );
        ''')
        conn.commit()

        backfill_locations_v5()


def backfill_locations_v4():
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT DISTINCT name, category, lot_number, expiration_date, dosage, form, ndc, location
            FROM items
            WHERE clinic_id = ?
        """, [session['clinic']])
        unique_keys = cur.fetchall()

        for key in unique_keys:
            key_fields = [
                key['name'], key['category'], key['lot_number'], key['expiration_date'],
                key['dosage'], key['form'], key['ndc'], key['location']
            ]

            # Step 2: Get all items that match this key (with different sublocations)
            cur.execute("""
                SELECT * FROM items
                WHERE name = ? AND category = ? AND lot_number = ? AND expiration_date = ?
                      AND dosage = ? AND form = ? AND ndc = ? AND location = ?
                ORDER BY id
            """, key_fields)
            matches = cur.fetchall()
            if not matches:
                continue


            # NEW Step 3: Choose the row with the most recent last_edit timestamp
            best = max(matches, key=lambda r: r['last_edit'] or '')

            # NEW Step 4: Fill in missing location1–4 fields from best (don't touch lot/exp)
            for row in matches:
                if row['id'] == best['id']:
                    continue

                updates = {}
                for f in ['location1', 'location2', 'location3', 'location4']:
                    if not row[f] and best[f]:
                        updates[f] = best[f]

                if updates:
                    set_clause = ", ".join(f"{k} = ?" for k in updates)
                    values = list(updates.values()) + [row['id']]
                    cur.execute(f"UPDATE items SET {set_clause} WHERE id = ?", values)
                    print(f"Updated ID {row['id']} with location fields: {list(updates.keys())}")


        cur.execute("""
            SELECT DISTINCT name, category, dosage, form, ndc,
                            location, lot_number, expiration_date,
                            location1, location2, location3, location4
            FROM items
            WHERE clinic_id = ?
        """, [session['clinic']])
        duplicate_keys = cur.fetchall()

        for key in duplicate_keys:
            key_fields = [
                key['name'], key['category'],
                key['dosage'], key['form'], key['ndc'], key['location'],
                key['lot_number'], key['expiration_date'],
                key['location1'], key['location2'], key['location3'], key['location4']
            ]

            cur.execute("""
                SELECT * FROM items
                WHERE name = ? AND category = ?
                      AND dosage = ? AND form = ? AND ndc = ? AND location = ?
                      AND lot_number = ? AND expiration_date = ?
                      AND location1 IS ? AND location2 IS ? AND location3 IS ? AND location4 IS ?
                ORDER BY id
            """, key_fields)
            dups = cur.fetchall()

            if len(dups) > 1:
                total_qty = sum(row['quantity'] for row in dups)
                keep_id = dups[0]['id']
                cur.execute("UPDATE items SET quantity = ? WHERE id = ?", [total_qty, keep_id])
                delete_ids = [row['id'] for row in dups[1:]]
                cur.executemany("DELETE FROM items WHERE id = ?", [(i,) for i in delete_ids])
                print(f"Deduplicated {len(dups)} → ID {keep_id} with quantity {total_qty}")


def backfill_locations_v5():


    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()


        print("Loading all items...")

        # Add clinic_id filter here
        cur.execute("SELECT * FROM items WHERE clinic_id = ?", [session['clinic']])
        all_items = cur.fetchall()

        print("Indexing items for location backfill...")
        key_to_items = defaultdict(list)
        for row in all_items: #NEW:5-2-26: addded location1-4
            key = (
                row['name'], row['category'], row['lot_number'], row['expiration_date'], row['location1'], row['location2'], row['location3'], row['location4'], 
                row['dosage'], row['form'], row['ndc'], row['location']
            )
            key_to_items[key].append(row)

        updates_needed = []

        for rows in key_to_items.values():
            if len(rows) < 2:
                continue
            best = max(rows, key=lambda r: r['last_edit'] or '')
            for row in rows:
                if row['id'] == best['id']:
                    continue
                update_fields = {}
                for f in ['location1', 'location2', 'location3', 'location4']:
                    if not row[f] and best[f]:
                        update_fields[f] = best[f]
                if update_fields:
                    updates_needed.append((update_fields, row['id']))

        print(f"Applying {len(updates_needed)} location field updates...")
        for update_fields, row_id in updates_needed:
            set_clause = ", ".join(f"{k} = ?" for k in update_fields)
            values = list(update_fields.values()) + [row_id]
            cur.execute(f"UPDATE items SET {set_clause} WHERE id = ?", values)

        print("Starting deduplication pass...")
        full_key_to_items = defaultdict(list)
        for row in all_items:
            key = (
                row['name'], row['category'], row['dosage'], row['form'], row['ndc'], row['location'], row['removed'],
                row['lot_number'], row['expiration_date'],
                row['location1'], row['location2'], row['location3'], row['location4']
            )
            full_key_to_items[key].append(row)

        for rows in full_key_to_items.values():
            if len(rows) <= 1:
                continue
            total_qty = sum(r['quantity'] for r in rows)
            keep_id = rows[0]['id']
            cur.execute("UPDATE items SET quantity = ? WHERE id = ?", (total_qty, keep_id))
            delete_ids = [(r['id'],) for r in rows[1:]]
            cur.executemany("DELETE FROM items WHERE id = ?", delete_ids)
            print(f"Deduplicated {len(rows)} → ID {keep_id} with quantity {total_qty}")


# Check if the user is logged in and is admin
def is_admin():
    return session.get('user') == 'admin'




# Path to JSON file storing users
USER_FILE = os.path.join(os.path.dirname(__file__), "users.json")
CLINIC_FILE = os.path.join(os.path.dirname(__file__), "clinics.json")

# The app uses one merged database and scopes rows by clinic_id.
DATABASE = os.path.join(DB_FOLDER, "merged.db")
DB_CONN = None

# Ensure the file exists
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump([], f, indent=4)


def clean_empty_values():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        # Delete empty location and category entries for the current clinic
        cur.execute("""
            DELETE FROM settings 
            WHERE (value = '' OR value IS NULL)
            AND clinic_id = ?
        """, (session['clinic'],))
        conn.commit()

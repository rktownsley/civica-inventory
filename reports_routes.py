from app_context import *

# This will print the medications and dosages of the selected location (availible in house)
@app.route('/print_inventory', methods=['GET', 'POST'])
def print_inventory():
    # Handle location and multiple category selection
    selected_location = request.args.get('location', '')
    selected_categories = request.args.getlist('categories')  # For multi-select

    query = """
        SELECT name, category, description, dosage, form, lot_number, ndc, dispense_used, unit_quantity,
            prescription_type, minimum_supply, location
        FROM items
        WHERE (removed = 0 OR removed IS NULL)
        AND clinic_id = ?
    """
    params = [session['clinic']]


    # Add location filter
    if selected_location:
        query += " AND location = ?"
        params.append(selected_location)

    # Add category filter if any selected
    if selected_categories:
        placeholders = ','.join(['?'] * len(selected_categories))
        query += f" AND category IN ({placeholders})"
        params.extend(selected_categories)

    # Run the final query
    medications = query_db(query, params)

    # Page title
    page_title = "Print Inventory"
    if selected_location:
        page_title += f" - {selected_location}"

    # Handle CSV download
    if 'download' in request.args:
        def generate_csv():
            yield 'Name,Category,Description,Dosage,Form,Lot Number,ND&C,Dispense Used,Unit Quantity,Prescription Type,Minimum Supply\n'
            for med in medications:
                yield f"{med['name']},{med['category']},{med['description']},{med['dosage']},{med['form']},{med['lot_number']},{med['ndc']},{med['dispense_used']},{med['unit_quantity']},{med['prescription_type']},{med['minimum_supply']}\n"

        current_date = datetime.now().strftime('%Y-%m-%d')
        filename = f'inventory_{selected_location}_{current_date}.csv' if selected_location else f'inventory_{current_date}.csv'

        return Response(generate_csv(), mimetype='text/csv', headers={
            'Content-Disposition': f'attachment; filename={filename}'
        })

    # Audit report can just reuse the same medications list
    audit_report = medications

    locations = query_db("SELECT DISTINCT location FROM items WHERE (removed = 0 OR removed IS NULL) AND clinic_id = ?", [session['clinic']])
    # Query for categories filtered by clinic_id
    categories_data = query_db("SELECT DISTINCT category FROM items WHERE category IS NOT NULL AND category != '' AND (removed = 0 OR removed IS NULL) AND clinic_id = ?", [session['clinic']])

    categories = [row['category'] for row in categories_data]

    return render_template('print_inventory.html',
                           medications=medications,
                           page_title=page_title,
                           locations=locations,
                           categories=categories,
                           selected_categories=selected_categories,
                           audit_report=audit_report)


@app.route('/audit_report', methods=['GET'])
def audit_report():
    selected_location = request.args.get('location', '')
    selected_filters = request.args.getlist('filters')
    # Today's date and 60 days from now in yyyy-mm-dd format
    today = datetime.today()
    today_str = today.strftime('%Y-%m-%d')
    sixty_days_str = (today + timedelta(days=60)).strftime('%Y-%m-%d')
    selected_last_edit = request.args.get('last_edits', '')
    selected_categories = request.args.getlist('categories')  # Allow multiple categories
    selected_suppliers = request.args.getlist('suppliers')  # Allow multiple suppliers
    selected_medication_classes = request.args.getlist('medication_classes')  # Allow multiple medication_classes
    selected_locations1 = request.args.getlist('locations1')  # Allow multiple locations1
    selected_locations2 = request.args.getlist('locations2')  # Allow multiple locations2
    selected_locations3 = request.args.getlist('locations3')  # Allow multiple locations3
    selected_locations4 = request.args.getlist('locations4')  # Allow multiple locations4
    search_term = request.args.get('search', '').strip()
    selected_sort = request.args.get('sort', '')

    query = """
        SELECT name, aka, category, supplier, description, dosage, form, lot_number, ndc, dispense_used, unit_quantity,
            prescription_type, minimum_supply, location, quantity, expiration_date, location1, location2, location3, location4, last_edit
        FROM items
        WHERE (removed = 0 OR removed IS NULL)
        AND clinic_id = ?
    """
    params = [session['clinic']]


    # Filter by location
    if selected_location:
        query += " AND (location = ?)"
        params.append(selected_location)

    # Apply E filter (low supply)
    if 'E' in selected_filters:
        query += " AND quantity < minimum_supply"


    # Check for expiration-related filters
    has_expired = 'F' in selected_filters
    has_expiring_soon = 'G' in selected_filters

    if has_expired or has_expiring_soon:
        # Always check expiration_date is present
        query += """
            AND expiration_date IS NOT NULL
            AND expiration_date != ''
        """

        # Reformat expiration_date to yyyy-mm-dd in SQL
        formatted_date_expr = """
            (SUBSTR(expiration_date, 7, 4) || '-' ||
            SUBSTR(expiration_date, 1, 2) || '-' ||
            SUBSTR(expiration_date, 4, 2))
        """

        if has_expired and has_expiring_soon:
            query += f"""
                AND (
                    {formatted_date_expr} < ?
                    OR {formatted_date_expr} BETWEEN ? AND ?
                )
            """
            params.extend([today_str, today_str, sixty_days_str])

        elif has_expired:
            query += f" AND {formatted_date_expr} < ?"
            params.append(today_str)

        elif has_expiring_soon:
            query += f" AND {formatted_date_expr} BETWEEN ? AND ?"
            params.extend([today_str, sixty_days_str])


    if selected_last_edit:
        try:
            # Ensure it's a valid date (YYYY-MM-DD)
            datetime.strptime(selected_last_edit, '%Y-%m-%d')

            # Compare full timestamp in SQL
            query += " AND last_edit >= ?"
            params.append(f"{selected_last_edit} 00:00:00")
        except ValueError:
            pass  # Invalid date format; ignore the filter


    # Filter by categories
    if selected_categories:
        placeholders = ','.join(['?'] * len(selected_categories))
        query += f" AND category IN ({placeholders})"
        params.extend(selected_categories)


    # Filter by suppliers
    if selected_suppliers:
        placeholders = ','.join(['?'] * len(selected_suppliers))
        query += f" AND supplier IN ({placeholders})"
        params.extend(selected_suppliers)

    # Filter by medication_classes
    if selected_medication_classes:
        placeholders = ','.join(['?'] * len(selected_medication_classes))
        query += f" AND medication_class IN ({placeholders})"
        params.extend(selected_medication_classes)

    # Filter by locations1
    if selected_locations1:
        placeholders = ','.join(['?'] * len(selected_locations1))
        query += f" AND location1 IN ({placeholders})"
        params.extend(selected_locations1)

    # Filter by locations2
    if selected_locations2:
        placeholders = ','.join(['?'] * len(selected_locations2))
        query += f" AND location2 IN ({placeholders})"
        params.extend(selected_locations2)

    # Filter by locations3
    if selected_locations3:
        placeholders = ','.join(['?'] * len(selected_locations3))
        query += f" AND location3 IN ({placeholders})"
        params.extend(selected_locations3)

    # Filter by locations4
    if selected_locations4:
        placeholders = ','.join(['?'] * len(selected_locations4))
        query += f" AND location4 IN ({placeholders})"
        params.extend(selected_locations4)

    if search_term:
        search_like = f"%{search_term.lower()}%"
        query += """
            AND (
                LOWER(name) LIKE ?
                OR LOWER(aka) LIKE ?
                OR LOWER(lot_number) LIKE ?
            )
        """
        params.extend([search_like, search_like, search_like])

    if selected_sort == 'sort1':
        query += " ORDER BY LOWER(name) ASC"
    elif selected_sort == 'sort2':
        query += " ORDER BY LOWER(name) DESC"
    elif selected_sort == 'sort5':
        query += " ORDER BY last_edit ASC"
    elif selected_sort == 'sort6':
        query += " ORDER BY last_edit DESC"
    else:
        query += " ORDER BY LOWER(name) ASC"


    # Run query
    medications = query_db(query, params)

    # Title and form data
    page_title = f"Audit Report - {selected_location}" if selected_location else "Audit Report"
    locations = query_db("SELECT DISTINCT location FROM items")

    return render_template('audit_report.html',
                           medications=medications,
                           page_title=page_title,
                           locations=locations,
                           selected_categories=selected_categories)


@app.route('/sort_page', methods=['GET'])
def sort_page():
    # Handle form submission to select a location
    selected_location = request.args.get('location', '')

    query = "SELECT * FROM items WHERE 1=1 AND clinic_id = ?"
    params = [session['clinic']]
    items = query_db(query, params)

    # Set the page title to include the location
    page_title = f"Item Report - {selected_location}" if selected_location else "Item Report"

    locations = query_db("SELECT DISTINCT location FROM items WHERE clinic_id = ?", [session['clinic']])

    # Render the items report page with items and page title
    return render_template('sort_page.html',
                           items=items,
                           page_title=page_title,
                           locations=locations)  # Pass items and locations to the template


@app.route('/sort_removed', methods=['GET'])
def sort_removed():
    # Handle form submission to select a location
    selected_location = request.args.get('location', '')

    query = "SELECT * FROM items WHERE 1=1 AND clinic_id = ?"
    params = [session['clinic']]
    items = query_db(query, params)

    # Set the page title to include the location
    page_title = f"Removed Item Report - {selected_location}" if selected_location else "Removed Item Report"

    locations = query_db("SELECT DISTINCT location FROM items WHERE clinic_id = ?", [session['clinic']])

    # Render the items report page with items and page title
    return render_template('sort_removed.html',
                           items=items,
                           page_title=page_title,
                           locations=locations)  # Pass items and locations to the template

@app.route('/download-inventory')
def download_inventory():
    current_dir = os.getcwd()
    last_found_db = None

    while True:
        db_path = os.path.join(current_dir, DATABASE)

        if os.path.isfile(db_path):
            # Keep updating the last found database path
            last_found_db = db_path

        # Move one level up
        parent_dir = os.path.dirname(current_dir)

        if parent_dir == current_dir:
            # Reached the root
            break

        current_dir = parent_dir

    if last_found_db:
        return send_file(last_found_db, as_attachment=True)
    else:
        abort(404)


@app.route('/download-messages')
def download_messages():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    last_found_db = None

    while True:
        db_path = os.path.join(current_dir, 'messages.json')

        if os.path.isfile(db_path):
            # Keep updating the last found database path
            last_found_db = db_path

        # Move one level up
        parent_dir = os.path.dirname(current_dir)

        if parent_dir == current_dir:
            # Reached the root
            break

        current_dir = parent_dir

    if last_found_db:
        return send_file(last_found_db, as_attachment=True)
    else:
        abort(404)


import zipfile
from io import BytesIO

@app.route('/download-all')
def download_all():

    if request.args.get("key") != "123":
        if request.args.get("key") != "456":
            abort(403)

    today = datetime.now().strftime("%Y-%m-%d")
    memory_file = BytesIO()
    folder = f"{today}/"

    # Construct absolute paths for all files
    base_dir = os.path.dirname(os.path.abspath(__file__))  # folder where app.py lives
    merged_db_path = os.path.join(base_dir, "user_databases", "merged.db")
    messages_path = os.path.join(base_dir, "messages.json")
    users_path = os.path.join(base_dir, "users.json")
    clinics_path = os.path.join(base_dir, "clinics.json")
    uploads_dir = os.path.join(base_dir, "static", "uploads")

    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        if os.path.isfile(merged_db_path):
            zf.write(merged_db_path, arcname=f"{folder}merged.db")
        else:
            print("Warning: merged.db not found!")

        if os.path.isfile(messages_path):
            zf.write(messages_path, arcname=f"{folder}messages.json")
        else:
            print("Warning: messages.json not found!")

        if os.path.isfile(users_path):
            zf.write(users_path, arcname=f"{folder}users.json")
        else:
            print("Warning: users.json not found!")
        
        if os.path.isfile(clinics_path):
            zf.write(clinics_path, arcname=f"{folder}clinics.json")
        else:
            print("Warning: clinics.json not found!")

        if request.args.get("key") != "123":
            # Add all files in static/uploads/ recursively
            if os.path.isdir(uploads_dir):
                for root, _, files in os.walk(uploads_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        # Preserve the uploads folder structure inside the ZIP
                        rel_path = os.path.relpath(full_path, base_dir)
                        zf.write(full_path, arcname=f"{folder}{rel_path}")
        else:
            print("Warning: this backup does not include photos. To include photos in the download, please use key=456")

    memory_file.seek(0)
    zip_filename = f"backup_{today}.zip"

    return send_file(
        memory_file,
        as_attachment=True,
        download_name=zip_filename,
        mimetype='application/zip'
    )


def send_inventory_email(recipient_emails, items, location=None):
    email_user = 'inventorynotificationbot@gmail.com'
    email_password = 'abvdmqdsasblfnda'
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587

    loc_label = f"{location}" if location else ""
    subject = f"{loc_label} Weekly Report ({datetime.now().strftime('%m/%d/%y')})"
    # If no items to restock, update the body
    if not items:
        body = "No items are requested."
    else:
        body = "These items are requested:\n\n" + "\n".join(items)

    msg = MIMEMultipart()
    msg['From'] = "Inventory Notification <inventorynotificationbot@gmail.com>"
    msg['To'] = ", ".join(recipient_emails)  # For display in email client
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.sendmail(email_user, recipient_emails, msg.as_string())  # Actual delivery
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False


@app.route("/send_restock_email", methods=["POST"])
def send_restock_email():
    data = request.get_json()
    recipient_raw = data.get("recipient")
    items = data.get("items", [])
    location = data.get("location")

    if not recipient_raw:
        return jsonify({"success": False, "error": "Missing data"}), 400

    # Split and clean the recipient list
    recipients = [email.strip() for email in recipient_raw.split(',') if email.strip()]

    success = send_inventory_email(recipients, items, location=location)
    return jsonify({"success": success})


def get_items_from_db():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, restock, location FROM items WHERE restock = 1")
        rows = cur.fetchall()
    items = [{"name": row[0], "restock": row[1], "location": row[2]} for row in rows]
    return items


@app.route('/get_items')
def get_items():
    # Fetch items from the database
    items = get_items_from_db()
    return jsonify(items)  # Return the items as a JSON response


@app.route("/send_weekly_restock_email")
def send_weekly_restock_email():
    items = get_items_from_db()

    # Group items by location
    items_by_location = {}
    for item in items:
        location = item.get("location", "").strip()
        if location not in items_by_location:
            items_by_location[location] = []
        if item["restock"] == 1:
            items_by_location[location].append(item["name"])

    location_emails = {
        "Tepati": "rktownsley@ucdavis.edu",
        "Knights Landing": "rktownsley@ucdavis.edu"
    }

    # Send emails to each known location
    success = True
    for location, recipient_str in location_emails.items():
        item_names = items_by_location.get(location, [])  # default to empty list
        recipients = [email.strip() for email in recipient_str.split(',') if email.strip()]
        email_sent = send_inventory_email(recipients, item_names, location=location)
        if not email_sent:
            success = False

    return jsonify({"success": success})


@app.route("/item_tracker")
def item_tracker():
    messages = load_messages()

    # Load users.json for mapping emails to full names
    with open(USER_FILE) as f:
        users_data = json.load(f)
    
    # Build a mapping: email -> full name
    email_to_fullname = {u['email']: u.get('fullname') for u in users_data if u.get('email')}

    # Add a display_name field to each message
    for msg in messages:
        if msg.get('username'):  # username exists, get full name from email if possible
            msg['display_name'] = email_to_fullname.get(msg['username'], msg['username'])
        else:  # fallback to user field
            msg['display_name'] = msg.get('user')

    # Filter messages based on session (same as before)
    if session.get('user') == 'admin' and session.get('clinic') == 'inventory':
        filtered_messages = [msg for msg in messages if msg['user'] in ['tepati', 'klohc', 'admin']]
    elif session.get('user') == 'admin':
        filtered_messages = [msg for msg in messages if msg['user'] == session.get('clinic')]
    else:
        filtered_messages = [msg for msg in messages if msg['user'] == session.get('user')]

    return render_template('item_tracker.html', messages=filtered_messages)


@app.route('/download_inventory_csv')
def download_inventory_csv():
    today_str = datetime.today().strftime('%Y-%m-%d')

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Select ALL columns, scoped to clinic
    cursor.execute("""
        SELECT *
        FROM items
        WHERE clinic_id = ?
    """, [session['clinic']])

    rows = cursor.fetchall()

    # Get column names automatically
    column_names = [description[0] for description in cursor.description]

    conn.close()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header row
    writer.writerow(column_names)

    # Write data rows
    for row in rows:
        writer.writerow(row)

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            "Content-Disposition": f"attachment; filename=audit_report_{today_str}.csv"
        }
    )


@app.route('/download_inventory_excel')
def download_inventory_excel():
    today_str = datetime.today().strftime('%Y-%m-%d')

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Select ALL columns, scoped to clinic
    cursor.execute("""
        SELECT *
        FROM items
        WHERE clinic_id = ?
    """, [session['clinic']])

    rows = cursor.fetchall()

    # Get column names automatically
    column_names = [desc[0] for desc in cursor.description]

    conn.close()

    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inventory"

    # Write header row
    ws.append(column_names)

    # Write data rows
    for row in rows:
        ws.append(row)

    # Auto-size columns (safe + optional)
    for col in ws.columns:
        max_length = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.value is not None:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_length + 2, 40)

    # Save to memory
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"audit_report_{today_str}.xlsx"
    )



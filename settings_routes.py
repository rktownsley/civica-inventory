from app_context import *
from inventory_routes import calculate_total_number_of_unique_items_in_inventory

def format_size(bytes):
    for unit in ['B','KB','MB','GB']:
        if bytes < 1024:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} TB"


@app.route('/settings', methods=['GET', 'POST'])
def settings():

    db_path = DATABASE
    log_path = MESSAGE_FILE  # wherever your messages JSON is

    db_bytes = os.path.getsize(db_path)
    log_bytes = os.path.getsize(log_path)

    db_size = format_size(os.path.getsize(db_path))
    log_size = format_size(os.path.getsize(log_path))

    # 🔍 DEBUG LOGGING
    print("=== FILE SIZE DEBUG ===")
    print(f"Database path: {db_path}")
    print(f"Database size: {db_bytes} bytes ({db_size})")
    print(f"Log file path: {log_path}")
    print(f"Log file size: {log_bytes} bytes ({log_size})")
    print("=======================")


    calculate_total_number_of_unique_items_in_inventory()
    total_items = session['total_unique_items']


    if request.method == 'POST':
        setting_type = request.form.get('type')
        value = request.form.get('value', '').strip()  # Trim any whitespace

        # Server-side validation to ensure no empty or whitespace-only submissions
        if not value:
            flash('Field cannot be empty', 'error')
            return redirect(url_for('settings',
        db_size=db_size,
        log_size=log_size))

        existing_item = query_db(
            "SELECT * FROM settings WHERE type = ? AND value = ? AND clinic_id = ?",
            [setting_type, value, session['clinic']],
            one=True
        )
        if existing_item:
            flash(f'{setting_type.capitalize()} "{value}" already exists!', 'warning')
        else:
            # Insert into the database only if valid
            # query_db("INSERT INTO settings (type, value) VALUES (?, ?)", [setting_type, value])
            query_db(
                "INSERT INTO settings (type, value, clinic_id) VALUES (?, ?, ?)",
                [setting_type, value, session['clinic']]
            )
            flash(f'{setting_type.capitalize()} "{value}" added successfully!', 'success')

        return redirect(url_for('settings',
        db_size=db_size,
        log_size=log_size))

    locations = query_db(
        "SELECT value FROM settings WHERE type = 'location' AND clinic_id = ?",
        [session['clinic']]
    )
    categories = query_db(
        "SELECT value FROM settings WHERE type = 'category' AND clinic_id = ?",
        [session['clinic']]
    )
    suppliers = query_db(
        "SELECT value FROM settings WHERE type = 'supplier' AND clinic_id = ?",
        [session['clinic']]
    )
    medication_classes = query_db(
        "SELECT value FROM settings WHERE type = 'medication_class' AND clinic_id = ?",
        [session['clinic']]
    )
    units = query_db(
        "SELECT value FROM settings WHERE type = 'dispense_used' AND clinic_id = ?",
        [session['clinic']]
    )
    dispenses = query_db(
        "SELECT value FROM settings WHERE type = 'dispense_as' AND clinic_id = ?",
        [session['clinic']]
    )
    forms = query_db(
        "SELECT value FROM settings WHERE type = 'form' AND clinic_id = ?",
        [session['clinic']]
    )

    print("HELLO LINE 3920")
    # Load users from JSON (NEW: 2-08-26)
    try:
        with open(USER_FILE, "r") as f:
            users = json.load(f)
    except Exception as e:
        flash("Internal server error loading users.", "error")
        return redirect(url_for("login"))
    
    clinic_users = [u for u in users if u['clinic_affiliation'] == session['clinic']]

    return render_template('settings.html', clinic_users=clinic_users,
        db_size=db_size,
        log_size=log_size, locations=locations, categories=categories, suppliers=suppliers, medication_classes=medication_classes, units=units, dispenses=dispenses, forms=forms, total_items=total_items)

@app.route("/update_user_roles", methods=["POST"])
def update_user_roles():
    print("HELLO LINE 3937")
    updated_roles = request.json
    try:
        with open(USER_FILE, "r") as f:
            users = json.load(f)

        for u in users:
            if u["email"] in updated_roles:
                print(f"Updating {u['email']} to {updated_roles[u['email']]}")
                u["role"] = updated_roles[u["email"]]

        with open(USER_FILE, "w") as f:
            json.dump(users, f, indent=2)

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/delete_location/<location_value>', methods=['POST'])
def delete_location(location_value):
    location_name = query_db(
        "SELECT value FROM settings WHERE type = 'location' AND value = ? AND clinic_id = ?",
        [location_value, session['clinic']],
        one=True
    )

    if location_name:
        # Delete the location entry that matches the 'value' field
        # query_db("DELETE FROM settings WHERE type = 'location' AND value = ?", [location_value])
        query_db(
            "DELETE FROM settings WHERE type = 'location' AND value = ? AND clinic_id = ?",
            [location_value, session['clinic']]
        )
        flash(f'Location "{location_value}" deleted successfully!', 'success')
    else:
        flash('Location not found!', 'error')

    return redirect(url_for('settings'))


#make this one to become view_location
@app.route('/view_location/<location_value>', methods=['GET', 'POST'])
def view_location(location_value):
    location = query_db(
        "SELECT * FROM settings WHERE type = 'location' AND value = ? AND clinic_id = ?",
        [location_value, session['clinic']],
        one=True
    )

    if request.method == 'POST':
        setting_type = request.form.get('type')
        value = request.form.get('value', '').strip()  # Trim any whitespace

        # Server-side validation to ensure no empty or whitespace-only submissions
        if not value:
            flash('Field cannot be empty', 'error')
            return redirect(url_for('view_location', location_value=location_value))

        existing_item = query_db(
            "SELECT * FROM locs WHERE type = ? AND value = ? AND site = ? AND clinic_id = ?", [setting_type, value, location_value, session['clinic']], one=True
        )
        if existing_item:
            flash(f'{setting_type.capitalize()} "{value}" already exists!', 'warning')
        else:
            # Insert into the database only if valid
            # query_db("INSERT INTO locs (type, value, site) VALUES (?, ?, ?)", [setting_type, value, location_value])
            query_db(
                "INSERT INTO locs (type, value, site, clinic_id) VALUES (?, ?, ?, ?)",
                [setting_type, value, location_value, session['clinic']]
            )
            flash(f'{setting_type.capitalize()} "{value}" added successfully!', 'success')

        return redirect(url_for('view_location', location_value=location_value))

    locations1 = query_db(
        "SELECT value FROM locs WHERE type = 'location1' AND site = ? AND clinic_id = ?",
        [location_value, session['clinic']]
    )
    locations2 = query_db(
        "SELECT value FROM locs WHERE type = 'location2' AND site = ? AND clinic_id = ?",
        [location_value, session['clinic']]
    )
    locations3 = query_db(
        "SELECT value FROM locs WHERE type = 'location3' AND site = ? AND clinic_id = ?",
        [location_value, session['clinic']]
    )
    locations4 = query_db(
        "SELECT value FROM locs WHERE type = 'location4' AND site = ? AND clinic_id = ?",
        [location_value, session['clinic']]
    )


    return render_template('view_location.html', location=location, locations1=locations1, locations2=locations2, locations3=locations3, locations4=locations4)


@app.route('/delete_location1/<location_value>', methods=['POST'])
def delete_location1(location_value):
    # Get the 'site' parameter from the form
    site = request.form.get('site')

    if not site:
        flash('Site not provided!', 'error')
        return redirect(url_for('settings'))

    location_name = query_db(
        "SELECT value FROM locs WHERE type = 'location1' AND value = ? AND site = ? AND clinic_id = ?",
        [location_value, site, session['clinic']],
        one=True
    )

    if location_name:
        # Delete the location entry that matches the 'value' field
        # query_db("DELETE FROM locs WHERE type = 'location1' AND value = ? AND site = ?", [location_value, site])
        query_db(
            "DELETE FROM locs WHERE type = 'location1' AND value = ? AND site = ? AND clinic_id = ?",
            [location_value, site, session['clinic']]
        )

        flash(f'Location "{location_value}" deleted successfully!', 'success')
    else:
        flash('Location not found!', 'error')

    return redirect(url_for('view_location', location_value=site))

@app.route('/delete_location2/<location_value>', methods=['POST'])
def delete_location2(location_value):
    # Get the 'site' parameter from the form
    site = request.form.get('site')

    if not site:
        flash('Site not provided!', 'error')
        return redirect(url_for('settings'))

    location_name = query_db(
        "SELECT value FROM locs WHERE type = 'location2' AND value = ? AND site = ? AND clinic_id = ?",
        [location_value, site, session['clinic']],
        one=True
    )

    if location_name:
        # Delete the location entry that matches the 'value' field
        # query_db("DELETE FROM locs WHERE type = 'location2' AND value = ? AND site = ?", [location_value, site])
        query_db(
            "DELETE FROM locs WHERE type = 'location2' AND value = ? AND site = ? AND clinic_id = ?",
            [location_value, site, session['clinic']]
        )

        flash(f'Location "{location_value}" deleted successfully!', 'success')
    else:
        flash('Location not found!', 'error')

    return redirect(url_for('view_location', location_value=site))

@app.route('/delete_location3/<location_value>', methods=['POST'])
def delete_location3(location_value):
    # Get the 'site' parameter from the form
    site = request.form.get('site')

    if not site:
        flash('Site not provided!', 'error')
        return redirect(url_for('settings'))

    location_name = query_db(
        "SELECT value FROM locs WHERE type = 'location3' AND value = ? AND site = ? AND clinic_id = ?",
        [location_value, site, session['clinic']],
        one=True
    )

    if location_name:
        # Delete the location entry that matches the 'value' field
        # query_db("DELETE FROM locs WHERE type = 'location3' AND value = ? AND site = ?", [location_value, site])
        query_db(
            "DELETE FROM locs WHERE type = 'location3' AND value = ? AND site = ? AND clinic_id = ?",
            [location_value, site, session['clinic']]
        )
        flash(f'Location "{location_value}" deleted successfully!', 'success')
    else:
        flash('Location not found!', 'error')

    return redirect(url_for('view_location', location_value=site))

@app.route('/delete_location4/<location_value>', methods=['POST'])
def delete_location4(location_value):
    # Get the 'site' parameter from the form
    site = request.form.get('site')

    if not site:
        flash('Site not provided!', 'error')
        return redirect(url_for('settings'))

    location_name = query_db(
        "SELECT value FROM locs WHERE type = 'location4' AND value = ? AND site = ? AND clinic_id = ?",
        [location_value, site, session['clinic']],
        one=True
    )


    if location_name:
        # Delete the location entry that matches the 'value' field
        # query_db("DELETE FROM locs WHERE type = 'location4' AND value = ? AND site = ?", [location_value, site])
        query_db(
            "DELETE FROM locs WHERE type = 'location4' AND value = ? AND site = ? AND clinic_id = ?",
            [location_value, site, session['clinic']]
        )

        flash(f'Location "{location_value}" deleted successfully!', 'success')
    else:
        flash('Location not found!', 'error')

    return redirect(url_for('view_location', location_value=site))


@app.route('/delete_category/<category_value>', methods=['POST'])
def delete_category(category_value):
    category_name = query_db(
        "SELECT value FROM settings WHERE type = 'category' AND value = ? AND clinic_id = ?",
        [category_value, session['clinic']],
        one=True
    )


    if category_name:
        # Delete the category entry that matches the 'value' field
        # query_db("DELETE FROM settings WHERE type = 'category' AND value = ?", [category_value])
        query_db(
            "DELETE FROM settings WHERE type = 'category' AND value = ? AND clinic_id = ?",
            [category_value, session['clinic']]
        )

        flash(f'Category "{category_value}" deleted successfully!', 'success')
    else:
        flash('Category not found!', 'error')

    return redirect(url_for('settings'))


@app.route('/delete_supplier/<supplier_value>', methods=['POST'])
def delete_supplier(supplier_value):
    supplier_name = query_db(
        "SELECT value FROM settings WHERE type = 'supplier' AND value = ? AND clinic_id = ?",
        [supplier_value, session['clinic']],
        one=True
    )


    if supplier_name:
        # Delete the supplier entry that matches the 'value' field
        # query_db("DELETE FROM settings WHERE type = 'supplier' AND value = ?", [supplier_value])
        query_db(
            "DELETE FROM settings WHERE type = 'supplier' AND value = ? AND clinic_id = ?",
            [supplier_value, session['clinic']]
        )

        flash(f'Supplier "{supplier_value}" deleted successfully!', 'success')
    else:
        flash('Supplier not found!', 'error')

    return redirect(url_for('settings'))


@app.route('/delete_medication_class/<medication_class_value>', methods=['POST'])
def delete_medication_class(medication_class_value):
    medication_class_name = query_db(
        "SELECT value FROM settings WHERE type = 'medication_class' AND value = ? AND clinic_id = ?",
        [medication_class_value, session['clinic']],
        one=True
    )


    if medication_class_name:
        # Delete the medication_class entry that matches the 'value' field
        # query_db("DELETE FROM settings WHERE type = 'medication_class' AND value = ?", [medication_class_value])
        query_db(
            "DELETE FROM settings WHERE type = 'medication_class' AND value = ? AND clinic_id = ?",
            [medication_class_value, session['clinic']]
        )

        flash(f'Medication Class "{medication_class_value}" deleted successfully!', 'success')
    else:
        flash('Medication Class not found!', 'error')

    return redirect(url_for('settings'))
    

@app.route('/edit_location/<location_value>', methods=['POST'])
def edit_location(location_value):
    # Get the new location name from the form
    new_location_value = request.form['value'].strip()

    # Update the location value in the database
    if new_location_value:
        query_db(
            "UPDATE settings SET value = ? WHERE type = 'location' AND value = ? AND clinic_id = ?",
            [new_location_value, location_value, session['clinic']]
        )

        flash(f'Site "{new_location_value}" updated successfully!', 'success')

        # Update the location for all items that have this location name
        # query_db('UPDATE items SET location = ? WHERE location = ?', (new_location_value, location_value))
        query_db(
            'UPDATE items SET location = ? WHERE location = ? AND clinic_id = ?',
            (new_location_value, location_value, session['clinic'])
        )


    else:
        flash('Site name cannot be empty!', 'error')

    return redirect(url_for('settings'))  # Redirect back to settings page


@app.route('/edit_supplier/<supplier_value>', methods=['POST'])
def edit_supplier(supplier_value):
    # Get the new supplier name from the form
    new_supplier_value = request.form['value'].strip()

    # Update the supplier value in the database
    if new_supplier_value:
        query_db(
            "UPDATE settings SET value = ? WHERE type = 'supplier' AND value = ? AND clinic_id = ?",
            [new_supplier_value, supplier_value, session['clinic']]
        )

        flash(f'Supplier "{new_supplier_value}" updated successfully!', 'success')

        # Update the supplier for all items that have this suppliers name
        # query_db('UPDATE items SET supplier = ? WHERE supplier = ?', (new_supplier_value, supplier_value))
        query_db(
            "UPDATE items SET supplier = ? WHERE supplier = ? AND clinic_id = ?",
            (new_supplier_value, supplier_value, session['clinic'])
        )


    else:
        flash('Supplier name cannot be empty!', 'error')

    return redirect(url_for('settings'))  # Redirect back to settings page


@app.route('/edit_medication_class/<medication_class_value>', methods=['POST'])
def edit_medication_class(medication_class_value):
    # Get the new medication_class name from the form
    new_medication_class_value = request.form['value'].strip()

    # Update the medication_class value in the database
    if new_medication_class_value:
        query_db(
            "UPDATE settings SET value = ? WHERE type = 'medication_class' AND value = ? AND clinic_id = ?",
            [new_medication_class_value, medication_class_value, session['clinic']]
        )

        flash(f'Medication Class "{new_medication_class_value}" updated successfully!', 'success')

        # Update the medication_class for all items that have this medication_classes name
        # query_db('UPDATE items SET medication_class = ? WHERE medication_class = ?', (new_medication_class_value, medication_class_value))
        query_db(
            "UPDATE items SET medication_class = ? WHERE medication_class = ? AND clinic_id = ?",
            [new_medication_class_value, medication_class_value, session['clinic']]
        )


    else:
        flash('Medication Class name cannot be empty!', 'error')

    return redirect(url_for('settings'))  # Redirect back to settings page


@app.route('/edit_category/<category_value>', methods=['POST'])
def edit_category(category_value):
    # Get the new category name from the form
    new_category_value = request.form['value'].strip()

    # Update the category value in the database
    if new_category_value:
        query_db(
            "UPDATE settings SET value = ? WHERE type = 'category' AND value = ? AND clinic_id = ?",
            [new_category_value, category_value, session['clinic']]
        )

        flash(f'Category "{new_category_value}" updated successfully!', 'success')

        # Update the category for all items that have this category name
        # query_db('UPDATE items SET category = ? WHERE category = ?', (new_category_value, category_value))
        query_db(
            "UPDATE items SET category = ? WHERE category = ? AND clinic_id = ?",
            (new_category_value, category_value, session['clinic'])
        )


    else:
        flash('Category name cannot be empty!', 'error')

    return redirect(url_for('settings'))  # Redirect back to settings page

@app.route('/edit_unit/<unit_value>', methods=['POST'])
def edit_unit(unit_value):
    # Get the new unit name from the form
    new_unit_value = request.form['value'].strip()

    # Update the unit value in the database
    if new_unit_value:
        query_db(
            "UPDATE settings SET value = ? WHERE type = 'dispense_used' AND value = ? AND clinic_id = ?",
            [new_unit_value, unit_value, session['clinic']]
        )

        flash(f'Unit "{new_unit_value}" updated successfully!', 'success')

        # Update the unit for all items that have this unit name
        # query_db('UPDATE items SET dispense_used = ? WHERE dispense_used = ?', (new_unit_value, unit_value))
        query_db(
            'UPDATE items SET dispense_used = ? WHERE dispense_used = ? AND clinic_id = ?',
            (new_unit_value, unit_value, session['clinic'])
        )


    else:
        flash('Unit name cannot be empty!', 'error')

    return redirect(url_for('settings'))  # Redirect back to settings page


@app.route('/edit_dispense/<dispense_value>', methods=['POST'])
def edit_dispense(dispense_value):
    # Get the new dispense name from the form
    new_dispense_value = request.form['value'].strip()

    # Update the dispense value in the database
    if new_dispense_value:
        query_db(
            "UPDATE settings SET value = ? WHERE type = 'dispense_as' AND value = ? AND clinic_id = ?",
            [new_dispense_value, dispense_value, session['clinic']]
        )

        flash(f'Unit "{new_dispense_value}" updated successfully!', 'success')

        # Update the dispense for all items that have this dispense name
        # query_db('UPDATE items SET dispense_as = ? WHERE dispense_as = ?', (new_dispense_value, dispense_value))
        query_db(
            'UPDATE items SET dispense_as = ? WHERE dispense_as = ? AND clinic_id = ?',
            (new_dispense_value, dispense_value, session['clinic'])
        )


    else:
        flash('Dispense name cannot be empty!', 'error')

    return redirect(url_for('settings'))  # Redirect back to settings page


@app.route('/edit_form/<form_value>', methods=['POST'])
def edit_form(form_value):
    # Get the new form name from the form
    new_form_value = request.form['value'].strip()

    # Update the for value in the database
    if new_form_value:
        query_db(
            "UPDATE settings SET value = ? WHERE type = 'form' AND value = ? AND clinic_id = ?",
            [new_form_value, form_value, session['clinic']]
        )

        flash(f'Form "{new_form_value}" updated successfully!', 'success')

        # Update the form for all items that have this form name
        # query_db('UPDATE items SET form = ? WHERE form = ?', (new_form_value, form_value))
        query_db(
            'UPDATE items SET form = ? WHERE form = ? AND clinic_id = ?',
            (new_form_value, form_value, session['clinic'])
        )


    else:
        flash('Form name cannot be empty!', 'error')

    return redirect(url_for('settings'))  # Redirect back to settings page


@app.route('/edit_location1/<location_value>', methods=['POST'])
def edit_location1(location_value):
    # Get the new location value from the form
    new_location1_value = request.form.get('value')
    site = request.form.get('site')

    if not site:
        flash('Site not provided!', 'error')
        return redirect(url_for('settings'))

    if not new_location1_value:
        flash('New location value not provided!', 'error')
        return redirect(url_for('view_location', location_value=site))

    location_name = query_db(
        "SELECT value FROM locs WHERE type = 'location1' AND value = ? AND site = ? AND clinic_id = ?",
        [location_value, site, session['clinic']], 
        one=True
    )

    if location_name:
        # Update the location value
        # query_db("UPDATE locs SET value = ? WHERE type = 'location1' AND value = ? AND site = ?", [new_location1_value, location_value, site])
        query_db(
            "UPDATE locs SET value = ? WHERE type = 'location1' AND value = ? AND site = ? AND clinic_id = ?",
            [new_location1_value, location_value, site, session['clinic']]
        )

        flash(f'Location 1 "{new_location1_value}" updated successfully!', 'success')

        # Update all items that have this location1 name
        # query_db('UPDATE items SET location1 = ? WHERE location1 = ? AND location = ?', [new_location1_value, location_value, site])
        query_db(
            'UPDATE items SET location1 = ? WHERE location1 = ? AND location = ? AND clinic_id = ?',
            [new_location1_value, location_value, site, session['clinic']]
        )


    else:
        flash('Location not found!', 'error')

    return redirect(url_for('view_location', location_value=site))


@app.route('/edit_location2/<location_value>', methods=['POST'])
def edit_location2(location_value):
    # Get the new location value from the form
    new_location2_value = request.form.get('value')
    site = request.form.get('site')

    if not site:
        flash('Site not provided!', 'error')
        return redirect(url_for('settings'))

    if not new_location2_value:
        flash('New location value not provided!', 'error')
        return redirect(url_for('view_location', location_value=site))

    location_name = query_db(
        "SELECT value FROM locs WHERE type = 'location2' AND value = ? AND site = ? AND clinic_id = ?",
        [location_value, site, session['clinic']], 
        one=True
    )

    if location_name:
        # Update the location value
        # query_db("UPDATE locs SET value = ? WHERE type = 'location2' AND value = ? AND site = ?", [new_location2_value, location_value, site])
        query_db(
            "UPDATE locs SET value = ? WHERE type = 'location2' AND value = ? AND site = ? AND clinic_id = ?",
            [new_location2_value, location_value, site, session['clinic']]
        )

        flash(f'Location 1 "{new_location2_value}" updated successfully!', 'success')

        # Update all items that have this location2 name
        # query_db('UPDATE items SET location2 = ? WHERE location2 = ? AND location = ?', [new_location2_value, location_value, site])
        query_db(
            'UPDATE items SET location2 = ? WHERE location2 = ? AND location = ? AND clinic_id = ?',
            [new_location2_value, location_value, site, session['clinic']]
        )


    else:
        flash('Location not found!', 'error')

    return redirect(url_for('view_location', location_value=site))


@app.route('/edit_location3/<location_value>', methods=['POST'])
def edit_location3(location_value):
    # Get the new location value from the form
    new_location3_value = request.form.get('value')
    site = request.form.get('site')

    if not site:
        flash('Site not provided!', 'error')
        return redirect(url_for('settings'))

    if not new_location3_value:
        flash('New location value not provided!', 'error')
        return redirect(url_for('view_location', location_value=site))

    location_name = query_db(
        "SELECT value FROM locs WHERE type = 'location3' AND value = ? AND site = ? AND clinic_id = ?",
        [location_value, site, session['clinic']],
        one=True
    )

    if location_name:
        # Update the location value
        # query_db("UPDATE locs SET value = ? WHERE type = 'location3' AND value = ? AND site = ?", [new_location3_value, location_value, site])
        query_db(
            "UPDATE locs SET value = ? WHERE type = 'location3' AND value = ? AND site = ? AND clinic_id = ?",
            [new_location3_value, location_value, site, session['clinic']]
        )

        flash(f'Location 1 "{new_location3_value}" updated successfully!', 'success')

        # Update all items that have this location3 name
        # query_db('UPDATE items SET location3 = ? WHERE location3 = ? AND location = ?', [new_location3_value, location_value, site])
        query_db(
            'UPDATE items SET location3 = ? WHERE location3 = ? AND location = ? AND clinic_id = ?',
            [new_location3_value, location_value, site, session['clinic']]
        )


    else:
        flash('Location not found!', 'error')

    return redirect(url_for('view_location', location_value=site))

@app.route('/edit_location4/<location_value>', methods=['POST'])
def edit_location4(location_value):
    # Get the new location value from the form
    new_location4_value = request.form.get('value')
    site = request.form.get('site')

    if not site:
        flash('Site not provided!', 'error')
        return redirect(url_for('settings'))

    if not new_location4_value:
        flash('New location value not provided!', 'error')
        return redirect(url_for('view_location', location_value=site))

    location_name = query_db(
        "SELECT value FROM locs WHERE type = 'location4' AND value = ? AND site = ? AND clinic_id = ?",
        [location_value, site, session['clinic']], 
        one=True
    )

    if location_name:
        # Update the location value
        # query_db("UPDATE locs SET value = ? WHERE type = 'location4' AND value = ? AND site = ?", [new_location4_value, location_value, site])
        query_db(
            "UPDATE locs SET value = ? WHERE type = 'location4' AND value = ? AND site = ? AND clinic_id = ?",
            [new_location4_value, location_value, site, session['clinic']]
        )

        flash(f'Location 1 "{new_location4_value}" updated successfully!', 'success')

        # Update all items that have this location4 name
        # query_db('UPDATE items SET location4 = ? WHERE location4 = ? AND location = ?', [new_location4_value, location_value, site])
        query_db(
            'UPDATE items SET location4 = ? WHERE location4 = ? AND location = ? AND clinic_id = ?',
            [new_location4_value, location_value, site, session['clinic']]
        )


    else:
        flash('Location not found!', 'error')

    return redirect(url_for('view_location', location_value=site))


@app.route('/delete_unit/<unit_value>', methods=['POST'])
def delete_unit(unit_value):
    unit_name = query_db(
        "SELECT value FROM settings WHERE type = 'dispense_used' AND value = ? AND clinic_id = ?",
        [unit_value, session['clinic']],
        one=True
    )


    if unit_name:
        # Delete the unit entry that matches the 'value' field
        # query_db("DELETE FROM settings WHERE type = 'dispense_used' AND value = ?", [unit_value])
        query_db(
            "DELETE FROM settings WHERE type = 'dispense_used' AND value = ? AND clinic_id = ?",
            [unit_value, session['clinic']]
        )

        flash(f'Unit "{unit_value}" deleted successfully!', 'success')
    else:
        flash('Unit not found!', 'error')

    return redirect(url_for('settings'))


@app.route('/delete_dispense/<dispense_value>', methods=['POST'])
def delete_dispense(dispense_value):
    dispense_name = query_db(
        "SELECT value FROM settings WHERE type = 'dispense_as' AND value = ? AND clinic_id = ?",
        [dispense_value, session['clinic']],
        one=True
    )


    if dispense_name:
        # Delete the dispense entry that matches the 'value' field
        # query_db("DELETE FROM settings WHERE type = 'dispense_as' AND value = ?", [dispense_value])
        query_db(
            "DELETE FROM settings WHERE type = 'dispense_as' AND value = ? AND clinic_id = ?",
            [dispense_value, session['clinic']]
        )

        flash(f'Dispense "{dispense_value}" deleted successfully!', 'success')
    else:
        flash('Dispense not found!', 'error')

    return redirect(url_for('settings'))


@app.route('/delete_form/<form_value>', methods=['POST'])
def delete_form(form_value):
    form_name = query_db(
        "SELECT value FROM settings WHERE type = 'form' AND value = ? AND clinic_id = ?",
        [form_value, session['clinic']],
        one=True
    )


    if form_name:
        # Delete the form entry that matches the 'value' field
        # query_db("DELETE FROM settings WHERE type = 'form' AND value = ?", [form_value])
        query_db(
            "DELETE FROM settings WHERE type = 'form' AND value = ? AND clinic_id = ?",
            [form_value, session['clinic']]
        )

        flash(f'Form "{form_value}" deleted successfully!', 'success')
    else:
        flash('Form not found!', 'error')

    return redirect(url_for('settings'))


@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    item = query_db(
        "SELECT * FROM items WHERE id = ? AND clinic_id = ?",
        [item_id, session['clinic']],
        one=True
    )


    original_name = item['name']  # 🆕 Save the original name
    original_supplier = item['supplier']
    original_medication_class = item['medication_class']
    original_category = item['category']
    original_expiration_date = item['expiration_date']
    original_dosage = item['dosage']
    original_form = item['form']
    original_lot_number = item['lot_number']
    original_ndc = item['ndc']

    original_name = item['name']
    original_aka = item['aka']
    original_status = item['status']
    original_quantity = item['quantity']
    original_location = item['location']
    original_location1 = item['location1']
    original_location2 = item['location2']
    original_location3 = item['location3']
    original_location4 = item['location4']
    original_category = item['category']
    original_description = item['description']
    original_instrument_type = item['instrument_type']
    original_expiration_date = item['expiration_date']
    original_supplier = item['supplier']
    original_medication_class = item['medication_class']
    original_order_number = item['order_number']
    original_dosage = item['dosage']
    original_form = item['form']
    original_lot_number = item['lot_number']
    original_ndc = item['ndc']
    original_dispense_used = item['dispense_used']
    original_dispense_as = item['dispense_as']
    original_unit_quantity = item['unit_quantity']
    original_prescription_type = item['prescription_type']
    original_minimum_supply = item['minimum_supply']
    original_photo_url = item['photo_url']

    search_query = request.args.get('search', '')  # Get search query from URL
    location_filter = request.args.get('location', '')  # Get selected location from URL

    if request.method == 'POST':
        # Basic fields
        name = request.form['name']
        aka = request.form['aka']
        status = request.form.get('status', '').strip()
        order_number = request.form['order_number']
        order_quantity = request.form['order_quantity']
        quantity = request.form['quantity']
        location = request.form.get('location', '')
        location1 = request.form.get('location1', '').strip()
        location2 = request.form.get('location2', '').strip()
        location3 = request.form.get('location3', '').strip()
        location4 = request.form.get('location4', '').strip()
        category = request.form['category']
        description = request.form['description']
        minimum_supply = request.form['minimum_supply']  # New field for minimum supply


        # Set the timezone to PST (Pacific Standard Time)
        pst_timezone = pytz.timezone('US/Pacific')

        # Get the current time in UTC and convert it to PST
        last_edit = datetime.now(pytz.utc).astimezone(pst_timezone).strftime('%Y-%m-%d %H:%M:%S')

        page = request.form.get('page', '')

        photo_url = None  # Default to None if no photo is uploaded

        # Initialize photo_url with current photo (in case no new photo is uploaded)
        photo_url = item['photo_url']

        # Handle file upload
        if 'item_photo' in request.files:
            file = request.files['item_photo']
            if file and allowed_file(file.filename):  # Check file type
                filename = secure_filename(file.filename)
                file.save(os.path.join(project_root, 'static', 'uploads', filename))
                photo_url = f'uploads/{filename}'  # Update photo_url with new file path

        # New fields (medication/surgical instrument specific)
        instrument_type = request.form.get('instrument_type', None)  # For surgical instruments
        expiration_date = request.form.get('expiration_date', None)  # For medications
        supplier = request.form.get('supplier', None)  # For medications
        medication_class = request.form.get('medication_class', None)  # For medications
        dosage = request.form.get('dosage', None)  # For medications
        form = request.form.get('form', None)  # For medications
        lot_number = request.form.get('lot_number', None)  # For medications
        ndc = request.form.get('ndc', None)  # For medications
        dispense_used = request.form.get('dispense_used', None)  # For medications
        dispense_as = request.form.get('dispense_as', None)  # For medications
        unit_quantity = request.form.get('unit_quantity', None)  # For medications
        prescription_type = request.form.get('prescription_type', None)  # For medications

        updates = []
        params = []

        if name != original_name:
            updates.append("name = ?")
            params.append(name)
        if category != original_category:
            updates.append("category = ?")
            params.append(category)
        if dosage != original_dosage:
            updates.append("dosage = ?")
            params.append(dosage)
        if form != original_form:
            updates.append("form = ?")
            params.append(form)
        if ndc != original_ndc:
            updates.append("ndc = ?")
            params.append(ndc)
        if aka != original_aka:
            updates.append("aka = ?")
            params.append(aka)
        if instrument_type != original_instrument_type:
            updates.append("instrument_type = ?")
            params.append(instrument_type)
        if photo_url != original_photo_url:
            updates.append("photo_url = ?")
            params.append(photo_url)
        if dispense_used != original_dispense_used:
            updates.append("dispense_used = ?")
            params.append(dispense_used)
        if dispense_as != original_dispense_as:
            updates.append("dispense_as = ?")
            params.append(dispense_as)
        if prescription_type != original_prescription_type:
            updates.append("prescription_type = ?")
            params.append(prescription_type)

        if updates:
            params += [
                original_name,
                original_category,
                original_dosage,
                original_form,
                original_ndc
            ]
            with sqlite3.connect(DATABASE) as conn:
                cur = conn.cursor()
                cur.execute(f"""
                    UPDATE items SET {', '.join(updates)}
                    WHERE name = ? AND category = ?
                    AND dosage = ? AND form = ? AND ndc = ?
                    AND clinic_id = ?
                """, params + [session['clinic']])  # Append the clinic_id from the session
                conn.commit()


        updates2 = []
        params2 = []
        if minimum_supply != original_minimum_supply:
            updates2.append("minimum_supply = ?")
            params2.append(minimum_supply)
        if updates2:
            params2 += [
                original_name,
                original_category,
                original_dosage,
                original_form,
                original_ndc,
                original_location
            ]
            with sqlite3.connect(DATABASE) as conn:
                cur = conn.cursor()
                cur.execute(f"""
                    UPDATE items SET {', '.join(updates2)}
                    WHERE name = ? AND category = ?
                    AND dosage = ? AND form = ? AND ndc = ? 
                    AND location = ? AND clinic_id = ?
                """, params2 + [session['clinic']])  # Append the clinic_id from the session
                conn.commit()


        query_db("""
            UPDATE items SET
            name = ?, aka = ?, status = ?, quantity = ?, location = ?, location1 = ?, location2 = ?, location3 = ?, location4 = ?, category = ?, description = ?,
            photo_url = ?, instrument_type = ?, expiration_date = ?, supplier = ?, medication_class = ?, order_number = ?, order_quantity = ?, dosage = ?, form = ?,
            lot_number = ?, ndc = ?, dispense_used = ?, dispense_as = ?, unit_quantity = ?, prescription_type = ?, minimum_supply = ?, last_edit = ?
            WHERE id = ? AND clinic_id = ?
        """, [name, aka, status, quantity, location, location1, location2, location3, location4, category, description, photo_url, instrument_type, expiration_date,
            supplier, medication_class, order_number, order_quantity, dosage, form, lot_number, ndc, dispense_used, dispense_as, unit_quantity, prescription_type, minimum_supply, last_edit, item_id, session['clinic']])


        # Get the referrer URL
        referrer = request.referrer

        if referrer:
            # Parse the referrer URL
            parsed_url = urlparse(referrer)

            # Modify the path part of the URL (replace 'edit_item' with 'view')
            new_path = parsed_url.path.replace('/edit_item/', '/view/', 1)

            # Rebuild the query string (keep existing query parameters)
            query_params = parse_qs(parsed_url.query)

            # Rebuild the full URL with the modified path
            new_url = parsed_url._replace(path=new_path, query=urlencode(query_params, doseq=True)).geturl()

            # Redirect to the new URL
            return redirect(new_url)


    locations = query_db("SELECT value FROM settings WHERE type = 'location' AND clinic_id = ?", [session['clinic']])
    categories = query_db("SELECT value FROM settings WHERE type = 'category' AND clinic_id = ?", [session['clinic']])
    suppliers = query_db("SELECT value FROM settings WHERE type = 'supplier' AND clinic_id = ?", [session['clinic']])
    medication_classes = query_db("SELECT value FROM settings WHERE type = 'medication_class' AND clinic_id = ?", [session['clinic']])
    units = query_db("SELECT value FROM settings WHERE type = 'dispense_used' AND clinic_id = ?", [session['clinic']])
    dispenses = query_db("SELECT value FROM settings WHERE type = 'dispense_as' AND clinic_id = ?", [session['clinic']])
    forms = query_db("SELECT value FROM settings WHERE type = 'form' AND clinic_id = ?", [session['clinic']])

    locations1 = query_db("SELECT value FROM locs WHERE type = 'location1' AND site = ? AND clinic_id = ?", 
                        [request.form.get('location', '') or '', session['clinic']])
    locations2 = query_db("SELECT value FROM locs WHERE type = 'location2' AND site = ? AND clinic_id = ?", 
                        [request.form.get('location', '') or '', session['clinic']])
    locations3 = query_db("SELECT value FROM locs WHERE type = 'location3' AND site = ? AND clinic_id = ?", 
                        [request.form.get('location', '') or '', session['clinic']])
    locations4 = query_db("SELECT value FROM locs WHERE type = 'location4' AND site = ? AND clinic_id = ?", 
                        [request.form.get('location', '') or '', session['clinic']])

    return render_template('edit_item.html', item=item, locations=locations, categories=categories, suppliers=suppliers, medication_classes=medication_classes, units=units, dispenses=dispenses, forms=forms, locations1=locations1, locations2=locations2,locations3=locations3, locations4=locations4, search=search_query, location=location_filter)


@app.route('/delete_photo', methods=['DELETE'])
def delete_photo():
    data = request.get_json()  # Get the JSON data from the request body
    photo_url = data.get("photo_url")

    if not photo_url:
        return jsonify({"error": "Photo URL is required"}), 400

    # Construct the path to the photo file
    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_url)

    # Check if the photo exists and delete it
    if os.path.exists(photo_path):
        os.remove(photo_path)  # Delete the file from the server
        return jsonify({"message": "Photo deleted successfully"}), 200
    else:
        return jsonify({"error": "Photo not found"}), 404


@app.route('/use_item/<int:item_id>', methods=['GET', 'POST'])
def use_item(item_id):
    item = query_db('SELECT * FROM items WHERE id = ? AND clinic_id = ?', [item_id, session['clinic']], one=True)

    search_query = request.args.get('search', '')  # Get search query from URL
    location_filter = request.args.get('location', '')  # Get selected location from URL

    if item is None:
        flash('Item not found', 'error')
        return redirect(url_for('home', search=search_query, location=location_filter))  # Or wherever you want to go if item not found

    if request.method == 'POST':
        quantity_used = int(request.form['quantity_used'])

        # Check if the quantity used is greater than the available quantity
        if quantity_used <= item['quantity']:
            new_quantity = item['quantity'] - quantity_used

            pst_timezone = pytz.timezone('US/Pacific')
            # Get the current time in UTC and convert it to PST
            last_edit = datetime.now(pytz.utc).astimezone(pst_timezone).strftime('%Y-%m-%d %H:%M:%S')

            # Update the item's quantity in the database
            # query_db('UPDATE items SET quantity = ? WHERE id = ?', [new_quantity, item_id])
            # query_db('UPDATE items SET quantity = ? WHERE id = ? AND clinic_id = ?', [new_quantity, item_id, session['clinic']])
            query_db('UPDATE items SET quantity = ?, last_edit = ? WHERE id = ? AND clinic_id = ?', [new_quantity, last_edit, item_id, session['clinic']])

            # Access min_level safely by checking if it exists
            min_level = item['minimum_supply']

            # Check if the min_level is present and if quantity is below the minimum level
            if new_quantity < min_level:
                flash('Warning: Quantity is getting low!', 'warning')
            else:
                flash(f"{quantity_used} item{'s were' if quantity_used != 1 else ' was'} successfully used!", "success")


            # log items used
            messages = load_messages()
            messages.append({
                "category": "log",
                "ts": datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M:%S"),
                # "user": f"{session['user']}",
                "user": session['user'] if session.get('clinic') == 'inventory' else session['clinic'],
                "username": session["username"],
                "action": f"used",
                "name": f"{item['name']}",
                "amount": f"{quantity_used}",
                "notes": ""
            })
            save_messages(messages)

            return redirect(request.referrer)

        else:
            flash('Not enough quantity available', 'error')
            return render_template('use_item.html', item=item, search=search_query, location=location_filter)  # Show an error if quantity used is too high

    return render_template('use_item.html', item=item, search=search_query, location=location_filter)


@app.route('/transfer_item/<int:item_id>', methods=['POST'])
def transfer_item(item_id):
    search_query = request.args.get('search', '')
    location_filter = request.args.get('location', '')

    item = query_db("SELECT * FROM items WHERE id = ? AND clinic_id = ?", [item_id, session['clinic']], one=True)

    original_location = item['location']

    # Set the timezone to PST (Pacific Standard Time)
    pst_timezone = pytz.timezone('US/Pacific')

    # Get the current time in UTC and convert it to PST
    last_edit = datetime.now(pytz.utc).astimezone(pst_timezone).strftime('%Y-%m-%d %H:%M:%S')

    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('main_page', search=search_query, location=location_filter))

    quantity_to_transfer = int(request.form['quantity_to_transfer'])
    new_location = request.form['new_location'].strip()

    if quantity_to_transfer > item['quantity']:
        flash('Cannot transfer more than the available quantity', 'error')
        return redirect(url_for('view_item', item_id=item_id, search=search_query, location=location_filter))

    query_db("UPDATE items SET quantity = quantity - ? WHERE id = ? AND clinic_id = ?", [quantity_to_transfer, item_id, session['clinic']])

    existing_item = query_db("""
        SELECT * FROM items WHERE name = ? AND location = ? AND category = ?
        AND IFNULL(expiration_date, '') = ? AND IFNULL(supplier, '') = ? AND IFNULL(medication_class, '') = ? AND IFNULL(order_number, '') = ? AND IFNULL(order_quantity, '') = ?
        AND IFNULL(dosage, '') = ? AND IFNULL(form, '') = ? AND IFNULL(lot_number, '') = ?
        AND IFNULL(ndc, '') = ? AND IFNULL(dispense_used, '') = ? AND IFNULL(dispense_as, '') = ? AND IFNULL(unit_quantity, '') = ?
        AND IFNULL(prescription_type, '') = ? AND IFNULL(instrument_type, '') = ?
        AND clinic_id = ?
    """, [item['name'], new_location, item['category'], item['expiration_date'], item['supplier'], item['medication_class'], item['order_number'], item['order_quantity'],
        item['dosage'], item['form'], item['lot_number'], item['ndc'], item['dispense_used'], item['dispense_as'],
        item['unit_quantity'], item['prescription_type'], item['instrument_type'], session['clinic']], one=True)


    existing_aggregated_item_at_new_location = query_db("""
        SELECT * FROM items WHERE name = ? AND location = ? AND category = ?
        AND IFNULL(dosage, '') = ? AND IFNULL(form, '') = ?
        AND IFNULL(ndc, '') = ?
        AND clinic_id = ?
    """, [item['name'], new_location, item['category'], 
        item['dosage'], item['form'], item['ndc'], 
        session['clinic']], one=True)


    if existing_item:
        query_db("""
            UPDATE items SET quantity = quantity + ?
            WHERE id = ? AND clinic_id = ?
        """, [quantity_to_transfer, existing_item['id'], session['clinic']])


    elif existing_aggregated_item_at_new_location:
        query_db("""
            INSERT INTO items (name, aka, status, quantity, location, category, description, photo_url, instrument_type,
                            expiration_date, supplier, medication_class, order_number, order_quantity, dosage, form, lot_number, ndc, dispense_used, dispense_as,
                            unit_quantity, prescription_type, minimum_supply, last_edit, location1, location2, location3, location4, clinic_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', '', '', ?)
        """, [item['name'], item['aka'], item['status'], quantity_to_transfer, new_location, item['category'], item['description'],
            item['photo_url'], item['instrument_type'], item['expiration_date'], item['supplier'], item['medication_class'], item['order_number'], item['order_quantity'],
            item['dosage'], item['form'], item['lot_number'], item['ndc'], item['dispense_used'], item['dispense_as'],
            item['unit_quantity'], item['prescription_type'], existing_aggregated_item_at_new_location['minimum_supply'], item['last_edit'],
            session['clinic']])


    else:
        query_db("""
            INSERT INTO items (name, aka, status, quantity, location, category, description, photo_url, instrument_type,
                            expiration_date, supplier, medication_class, order_number, order_quantity, dosage, form, lot_number, ndc, dispense_used, dispense_as,
                            unit_quantity, prescription_type, minimum_supply, last_edit, location1, location2, location3, location4, clinic_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', '', '', ?)
        """, [item['name'], item['aka'], item['status'], quantity_to_transfer, new_location, item['category'], item['description'],
            item['photo_url'], item['instrument_type'], item['expiration_date'], item['supplier'], item['medication_class'], item['order_number'], item['order_quantity'],
            item['dosage'], item['form'], item['lot_number'], item['ndc'], item['dispense_used'], item['dispense_as'],
            item['unit_quantity'], item['prescription_type'], item['minimum_supply'], item['last_edit'],
            session['clinic']])  # Add the clinic_id to the insert statement


    flash(f"Successfully transferred {quantity_to_transfer} of {item['name']} to {new_location}", 'success')

    # log items transferred
    messages = load_messages()

    # Replace 'Knights Landing' with 'KL' if present
    original_location_short = "KL" if original_location == "Knights Landing" else original_location
    new_location_short = "KL" if new_location == "Knights Landing" else new_location

    messages.append({
        # "user": f"{session['user']}",
        # "text": f"transferred {quantity_to_transfer} {item['name']} from {original_location} to {new_location}",
        # "category": "log",
        # "date": datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%Y-%m-%d @ %H:%M:%S")
        "category": "log",
        "ts": datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M:%S"),
        # "user": f"{session['user']}",
        "user": session['user'] if session.get('clinic') == 'inventory' else session['clinic'],
        "username": session["username"],
        "action": f"transferred",
        "name": f"{item['name']}",
        "amount": f"{quantity_to_transfer}",
        "notes": f"{original_location_short} to {new_location_short}"
    })
    save_messages(messages)


    return redirect(request.referrer)
    return redirect(url_for('main_page', search=search_query, location=location_filter))


@app.route('/autocomplete', methods=['GET'])
def autocomplete():


    ################################
    # Only display filtered results
    ################################

    search_query = request.args.get('search', '')  # Get search query from URL
    location_filter = request.args.get('location', '')  # Get selected location from URL

    #new
    location1_filter = request.args.get('location1', '')  # Get selected location from URL
    location2_filter = request.args.get('location2', '')  # Get selected location from URL
    location3_filter = request.args.get('location3', '')  # Get selected location from URL
    location4_filter = request.args.get('location4', '')  # Get selected location from URL

    category_filter = request.args.get('category', '')  # Get selected category from URL
    print("category filter:", {category_filter})
    print(request.args)
    supplier_filter = request.args.get('supplier', '')  # Get selected supplier from URL
    medication_class_filter = request.args.get('medication_class', '')  # Get selected medication_class from URL
    last_edit_filter = request.args.get('last_edit', '')  # Get selected supplier from URL
    sort_option = request.args.get('filter', '')  # Get selected sort option from URL
    sort_order = request.args.get('sort', '') #NEW:1-11-2026


    # Base query to get all items
    query = "SELECT * FROM items WHERE 1=1"
    params = []

    # Do not display items that have been removed
    query += " AND (removed = 0 OR removed IS NULL)"

    # 🔒 Filter by current clinic
    query += " AND clinic_id = ?"
    params.append(session['clinic'])

    # Apply search filter if search query exists
    if search_query:
        query += " AND (name LIKE ? OR aka LIKE ? OR lot_number LIKE ? OR order_number LIKE ?)"
        params.append('%' + search_query + '%')
        params.append('%' + search_query + '%')
        params.append('%' + search_query + '%')
        params.append('%' + search_query + '%')

    # Apply location filter if a location is selected
    if location_filter:
        query += " AND location = ?"
        params.append(location_filter)

    # Apply location1-location4 filters if selected
    if location1_filter:
        query += " AND location1 = ?"
        params.append(location1_filter)
    if location2_filter:
        query += " AND location2 = ?"
        params.append(location2_filter)
    if location3_filter:
        query += " AND location3 = ?"
        params.append(location3_filter)
    if location4_filter:
        query += " AND location4 = ?"
        params.append(location4_filter)


    # Apply category filter if a category is selected
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    # Apply supplier filter if a supplier is selected
    if supplier_filter:
        query += " AND supplier = ?"
        params.append(supplier_filter)

    # Apply medication_class filter if a medication_class is selected
    if medication_class_filter:
        query += " AND medication_class = ?"
        params.append(medication_class_filter)

    # Add the date filter if `date_filter` is provided
        # Show items that where last edited AFTER the selected date
    if last_edit_filter:
        query += " AND last_edit > ?"
        params.append(last_edit_filter)

    # Add order by clause for sorting
    if sort_option == 'E':
        query += " AND quantity < minimum_supply"

    if sort_order: #NEW:1-11-2026
        query += " AND sort = ?"
        params.append(sort_order)
        
    else:
    # Add order by clause to show the most recent items first
        #  query += " ORDER BY id DESC"
        query += " ORDER BY name COLLATE NOCASE ASC"


    # Fetch filtered items based on the query
    items = query_db(query, params)


    #################################
    #################################
    #################################

    filtered_item_ids = [item['id'] for item in items]
    print(f"query: {query}")
    print(f"params: {params}")
    print(f"item ids: {filtered_item_ids}")


    search_query = request.args.get('query', '')  # Get the query parameter from the GET request
    print(f"Searching for: {search_query}")  # Debugging line

    name_suggestions = query_db("""
        SELECT name FROM items 
        WHERE name LIKE ? 
        AND clinic_id = ?
    """, ('%' + search_query + '%', session['clinic']))
    names = [suggestion['name'] for suggestion in name_suggestions]  # Extract names from the result

    aka_suggestions = query_db("""
        SELECT aka FROM items 
        WHERE aka LIKE ? 
        AND clinic_id = ?
    """, ('%' + search_query + '%', session['clinic']))
    akas = [suggestion['aka'] for suggestion in aka_suggestions]  # Extract akas from the result

    lot_number_suggestions = query_db("""
        SELECT lot_number FROM items 
        WHERE lot_number LIKE ? 
        AND clinic_id = ?
    """, ('%' + search_query + '%', session['clinic']))
    lot_numbers = [suggestion['lot_number'] for suggestion in lot_number_suggestions]  # Extract lot numbers from the result

    order_numbers_suggestions = query_db("""
        SELECT order_number FROM items 
        WHERE order_number LIKE ? 
        AND clinic_id = ?
    """, ('%' + search_query + '%', session['clinic']))
    order_numbers = [suggestion['order_number'] for suggestion in order_numbers_suggestions]  # Extract order_numbers from the result

    # Combine both names and akas into one suggestions list
    suggestions = names + akas + lot_numbers + order_numbers

    print(f"Suggestions: {suggestions}")  # Debugging line
    return {'suggestions': suggestions}


# Clean up empty locations and categories from the database

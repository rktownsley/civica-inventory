from app_context import *

def prepare_location_display_data(item, itemsA, session_user):
    location_totals = {}
    for location_id, details in item['locations'].items():
        loc = details['location']
        qty = int(details['quantity'])
        location_totals[loc] = location_totals.get(loc, 0) + qty

    # Filter and deduplicate locations based on user access
    valid_locations = set()
    for _, details in item['locations'].items():
        details['total_quantity'] = location_totals[details['location']] #NEW
        loc = details['location']
        if session_user == 'tepati' and loc != 'Tepati' and loc != 'Grove':
            continue
        if session_user == 'klohc' and loc != 'Knights Landing' and loc != 'Grove':
            continue
        valid_locations.add(loc)

    # Sort all locations alphabetically except Grove
    sorted_locations = sorted([loc for loc in valid_locations if loc != 'Grove'])
    if 'Grove' in valid_locations:
        sorted_locations.append('Grove')

    # Prepare display data
    location_display_data = []
    for loc in sorted_locations:
        quantities = [
            int(other_item['quantity']) for other_item in itemsA
            if other_item['name'] == item['name'] and
               other_item['category'] == item['category'] and
               other_item['dosage'] == item['dosage'] and
               other_item['form'] == item['form'] and
               other_item['ndc'] == item['ndc'] and
               other_item['location'] == loc
        ]
        total_quantity = sum(quantities)

        valid_lots = [
            (lid, det) for lid, det in item['locations'].items()
            if det['location'] == loc and int(lid) >= 0
        ]
        is_disabled = len(valid_lots) == 0

        all_minimums = [
            int(det['minimum_supply']) for lid, det in item['locations'].items()
            if det['location'] == loc and 'minimum_supply' in det and det['minimum_supply']
        ]
        max_minimum = max(all_minimums) if all_minimums else 0
        show_low = (total_quantity < max_minimum) and not is_disabled

        location_display_data.append({
            'location': loc,
            'display_label': 'KL' if loc == 'Knights Landing' else loc,
            'total_quantity': total_quantity,
            'is_disabled': is_disabled,
            'show_low': show_low
        })

    return location_display_data


# helper function to calculate total number of unique items in inventory, for settings page (new: 2-13-26)
def calculate_total_number_of_unique_items_in_inventory():
    query = "SELECT * FROM items WHERE 1=1"
    params = []

    query += " AND (removed = 0 OR removed IS NULL)"
    query += " AND (delisted = 0 OR delisted IS NULL)"

    query += " AND clinic_id = ?"
    params.append(session['clinic'])

    items = query_db(query, params)
    unique_items = set()

    removed_items = query_db("SELECT * FROM items WHERE removed = ? AND delisted = 0 AND clinic_id = ?", [True, session['clinic']])
    # Create temporary copies and append if they pass filters
    for r in removed_items:
        temp = dict(r)
        temp['location'] = "REMOVED"
        temp['removed'] = None
        items.append(temp)

    session['total_unique_items'] = 0

    for item in items:
    
        key = (item['name'], item['category'], item['dosage'], item['form'], item['ndc'])

        if key not in unique_items:

            unique_items.add(key)

            session['total_unique_items'] += 1


# Routes
@app.route('/', methods=['GET'])
def main_page():

    set_clinic_database()
    init_db()

    if not session.get('clinic') or not session.get('user'):
        return redirect(url_for('login'))

    search_query = request.args.get('search', '')  # Get search query from URL
    location_filter = request.args.get('location', '')  # Get selected location from URL

    #new
    location1_filter = request.args.get('location1', '')  # Get selected location from URL
    location2_filter = request.args.get('location2', '')  # Get selected location from URL
    location3_filter = request.args.get('location3', '')  # Get selected location from URL
    location4_filter = request.args.get('location4', '')  # Get selected location from URL

    category_filter = request.args.get('category', '')  # Get selected category from URL
    supplier_filter = request.args.get('supplier', '')  # Get selected supplier from URL
    medication_class_filter = request.args.get('medication_class', '')  # Get selected medication_class from URL
    last_edit_filter = request.args.get('last_edit', '')  # Get selected supplier from URL
    sort_option = request.args.get('filter', '')  # Get selected sort option from URL
    sort_order = request.args.get('sort', '') #NEW

    selected_categories = request.args.getlist('categories')  # For multi-select
    selected_suppliers = request.args.getlist('suppliers')  # For multi-select
    selected_medication_classes = request.args.getlist('medication_classes')  # For multi-select
    selected_locations1 = request.args.getlist('locations1')  # For multi-select
    selected_locations2 = request.args.getlist('locations2')  # For multi-select
    selected_locations3 = request.args.getlist('locations3')  # For multi-select
    selected_locations4 = request.args.getlist('locations4')  # For multi-select
    last_edits_filter = request.args.get('last_edits', '')  # Get selected supplier from URL
    selected_filters = request.args.getlist('filters')  # Get selected supplier from URL


    # Get the current page from the query parameters (default is 1)
    page = request.args.get('page', '1')  # Ensure a string default value
    page = int(page) if page.isdigit() else 1


    # Base query to get all items
    query = "SELECT * FROM items WHERE 1=1"
    params = []

    # Base query to get an item from ALL locations
    queryA = "SELECT * FROM items WHERE 1=1"
    paramsA = []

    # Do not display items that have been removed
    query += " AND (removed = 0 OR removed IS NULL)"
    queryA += " AND (removed = 0 OR removed IS NULL)"

    # Do not display items that have been delisted (NEW 10/24/25)
    query += " AND (delisted = 0 OR delisted IS NULL)"
    queryA += " AND (delisted = 0 OR delisted IS NULL)"

    # 🔒 Filter by current clinic
    query += " AND clinic_id = ?"
    params.append(session['clinic'])

    queryA += " AND clinic_id = ?"
    paramsA.append(session['clinic'])


    # Apply search filter if search query exists
    if search_query:
        query += " AND (name LIKE ? OR aka LIKE ? OR lot_number LIKE ? OR order_number LIKE ?)"
        params.append('%' + search_query + '%')
        params.append('%' + search_query + '%')
        params.append('%' + search_query + '%')
        params.append('%' + search_query + '%')

        queryA += " AND (name LIKE ? OR aka LIKE ? OR lot_number LIKE ? OR order_number LIKE ?)"
        paramsA.append('%' + search_query + '%')
        paramsA.append('%' + search_query + '%')
        paramsA.append('%' + search_query + '%')
        paramsA.append('%' + search_query + '%')

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
        queryA += " AND category = ?"
        paramsA.append(category_filter)

    # Apply supplier filter if a supplier is selected
    if supplier_filter:
        query += " AND supplier = ?"
        params.append(supplier_filter)
        queryA += " AND supplier = ?"
        paramsA.append(supplier_filter)

    # Apply medication_class filter if a medication_class is selected
    if medication_class_filter:
        query += " AND medication_class = ?"
        params.append(medication_class_filter)
        queryA += " AND medication_class = ?"
        paramsA.append(medication_class_filter)

    # Add the date filter if `date_filter` is provided
        # Show items that where last edited AFTER the selected date
    if last_edit_filter:
        query += " AND last_edit > ?"
        params.append(last_edit_filter)
        queryA += " AND last_edit > ?"
        paramsA.append(last_edit_filter)


    # Add category filter if any selected
    if selected_categories:
        placeholders = ','.join(['?'] * len(selected_categories))
        query += f" AND category IN ({placeholders})"
        params.extend(selected_categories)

    if selected_suppliers:
        placeholders = ','.join(['?'] * len(selected_suppliers))
        query += f" AND supplier IN ({placeholders})"
        params.extend(selected_suppliers)

    if selected_medication_classes:
        placeholders = ','.join(['?'] * len(selected_medication_classes))
        query += f" AND medication_class IN ({placeholders})"
        params.extend(selected_medication_classes)

    if selected_locations1:
        placeholders = ','.join(['?'] * len(selected_locations1))
        query += f" AND location1 IN ({placeholders})"
        params.extend(selected_locations1)

    if selected_locations2:
        placeholders = ','.join(['?'] * len(selected_locations2))
        query += f" AND location2 IN ({placeholders})"
        params.extend(selected_locations2)

    if selected_locations3:
        placeholders = ','.join(['?'] * len(selected_locations3))
        query += f" AND location3 IN ({placeholders})"
        params.extend(selected_locations3)

    if selected_locations4:
        placeholders = ','.join(['?'] * len(selected_locations4))
        query += f" AND location4 IN ({placeholders})"
        params.extend(selected_locations4)

    if last_edits_filter:
        query += " AND last_edit > ?"
        params.append(last_edits_filter)
        queryA += " AND last_edit > ?"
        paramsA.append(last_edits_filter)


    #NEW
    today = datetime.today()
    one_month = today + timedelta(days=60)
    one_week = today + timedelta(days=7)
    four_week = today + timedelta(days=30)
    three_month = today + timedelta(days=90)
    # Manually format as YYYY-MM-DD
    today_str = f"{today.year}-{today.month:02d}-{today.day:02d}"
    one_month_str = f"{one_month.year}-{one_month.month:02d}-{one_month.day:02d}"
    one_week_str = f"{one_week.year}-{one_week.month:02d}-{one_week.day:02d}"
    four_week_str = f"{four_week.year}-{four_week.month:02d}-{four_week.day:02d}"
    three_month_str = f"{three_month.year}-{three_month.month:02d}-{three_month.day:02d}"
    if sort_option == 'F':  # Expired
        query += """
            AND DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) < ?
        """
        params.append(today_str)
    elif sort_option == 'G':  # Expiring within 60 days
        query += """
            AND DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) >= ?
            AND DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) < ?
        """
        params += [today_str, one_month_str]

    #NEW 3-29-26
    elif sort_option == 'I':  # Expiring within 7 days
        query += """
            AND DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) >= ?
            AND DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) < ?
        """
        params += [today_str, one_week_str]

    elif sort_option == 'J':  # Expiring within 30 days
        query += """
            AND DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) >= ?
            AND DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) < ?
        """
        params += [today_str, four_week_str]

    elif sort_option == 'K':  # Expiring within 90 days
        query += """
            AND DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) >= ?
            AND DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) < ?
        """
        params += [today_str, three_month_str]

    #NEW 2-01-2026
    elif sort_option == 'H':  # No expiration date
        query += """
            AND (expiration_date IS NULL OR expiration_date = '')
        """


    expiration_clauses = []
    expiration_params = []

    if 'F' in selected_filters:  # Expired
        expiration_clauses.append(
            "DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) < ?"
        )
        expiration_params.append(today_str)

    if 'G' in selected_filters:  # Expiring within 60 days
        expiration_clauses.append(
            "(DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) >= ? AND DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) < ?)"
        )
        expiration_params.extend([today_str, one_month_str])

    if 'I' in selected_filters:  # Expiring within 7 days (NEW: 3-29-26)
        expiration_clauses.append(
            "(DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) >= ? AND DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) < ?)"
        )
        expiration_params.extend([today_str, one_week_str])

    if 'J' in selected_filters:  # Expiring within 30 days (NEW: 3-29-26)
        expiration_clauses.append(
            "(DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) >= ? AND DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) < ?)"
        )
        expiration_params.extend([today_str, four_week_str])

    if 'K' in selected_filters:  # Expiring within 90 days (NEW: 3-29-26)
        expiration_clauses.append(
            "(DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) >= ? AND DATE(SUBSTR(expiration_date, 7, 4) || '-' || SUBSTR(expiration_date, 1, 2) || '-' || SUBSTR(expiration_date, 4, 2)) < ?)"
        )
        expiration_params.extend([today_str, three_month_str])


    if 'H' in selected_filters:  # No expiration date (NEW: 2-01-2026)
        expiration_clauses.append(
            "(expiration_date IS NULL OR expiration_date = '')"
        )


    if expiration_clauses:
        query += " AND (" + " OR ".join(expiration_clauses) + ")"
        params.extend(expiration_params)


    sort_map = {
        'sort1': 'name COLLATE NOCASE ASC',
        'sort2': 'name COLLATE NOCASE DESC',
        'sort5': 'last_edit COLLATE NOCASE ASC',
        'sort6': 'last_edit COLLATE NOCASE DESC',
    }

    sort = request.args.get('sort', 'sort1')

    if sort in sort_map:
        order_clause = sort_map.get(sort, sort_map['sort1'])
        query += f" ORDER BY {order_clause}"
        queryA += f" ORDER BY {order_clause}"

    else:
        query += " ORDER BY name COLLATE NOCASE ASC"
        queryA += " ORDER BY name COLLATE NOCASE ASC"


    # Fetch filtered items based on the query
    items = query_db(query, params)

    # Fetch the item where it exists at all locations
    itemsA = query_db(queryA, paramsA)


    # --- After you fetch the main items list (example variable 'items') ---

    removed_items = query_db("SELECT * FROM items WHERE removed = ? AND delisted = 0 AND clinic_id = ?", [True, session['clinic']])

    # Helper function to check if an item passes all filters
    def passes_filters(item):
        # Search filter
        if search_query:
            if not (
                search_query.lower() in (item.get('name') or '').lower() or
                search_query.lower() in (item.get('aka') or '').lower() or
                search_query.lower() in (item.get('lot_number') or '').lower() or
                search_query.lower() in (item.get('order_number') or '').lower()
            ):
                return False

        # Location filters
        if location_filter and item.get('location') != location_filter:
            return False
        if location1_filter and item.get('location1') != location1_filter:
            return False
        if location2_filter and item.get('location2') != location2_filter:
            return False
        if location3_filter and item.get('location3') != location3_filter:
            return False
        if location4_filter and item.get('location4') != location4_filter:
            return False

        # Multi-select filters
        if selected_categories and item.get('category') not in selected_categories:
            return False
        if selected_suppliers and item.get('supplier') not in selected_suppliers:
            return False
        if selected_medication_classes and item.get('medication_class') not in selected_medication_classes:
            return False
        if selected_locations1 and item.get('location1') not in selected_locations1:
            return False
        if selected_locations2 and item.get('location2') not in selected_locations2:
            return False
        if selected_locations3 and item.get('location3') not in selected_locations3:
            return False
        if selected_locations4 and item.get('location4') not in selected_locations4:
            return False


        # Last edit filter
        if last_edits_filter and item.get('last_edit'):
            last_edit_dt = datetime.strptime(item['last_edit'].split()[0], '%Y-%m-%d') #new 11/14/2025
            if last_edit_dt <= datetime.strptime(last_edits_filter, '%Y-%m-%d'):
                return False


        # Do not display any of the items in 'removed' if any of these filters are applied (new 11/14/2025)
        if 'F' in selected_filters:  # expired
            return False
        if 'G' in selected_filters:  # expiring soon
            return False
        if 'I' in selected_filters:  # expiring 7 days
            return False
        if 'J' in selected_filters:  # expiring 30 days
            return False
        if 'K' in selected_filters:  # expiring 90 days
            return False
        if 'E' in selected_filters:  # expiring soon
            return False
        if 'H' in selected_filters:  # does not expire
            return False


        return True

    # Create temporary copies and append if they pass filters
    for r in removed_items:
        temp = dict(r)
        temp['location'] = "REMOVED"
        temp['removed'] = None
        if passes_filters(temp):
            items.append(temp)

    # Sort temporary items using the same logic as SQL ORDER BY
    sort = request.args.get('sort', 'sort1')
    sort_map = {
        'sort1': 'name COLLATE NOCASE ASC',
        'sort2': 'name COLLATE NOCASE DESC',
        'sort5': 'last_edit COLLATE NOCASE ASC',
        'sort6': 'last_edit COLLATE NOCASE DESC',
    }

    # Python-side sort mimicking SQL ORDER BY
    if sort in sort_map:
        if 'DESC' in sort_map[sort]:
            reverse = True
        else:
            reverse = False

        if 'name' in sort_map[sort]:
            items.sort(key=lambda x: x['name'].lower(), reverse=reverse)
        elif 'last_edit' in sort_map[sort]:
            items.sort(key=lambda x: x['last_edit'] or '', reverse=reverse)
    else:
        items.sort(key=lambda x: x['name'].lower())  # default ascending


    # Create a list to hold the aggregated items
    aggregated_items = []

    # A set to track the unique combinations of (name, supplier, category) we've processed
    seen_items = set()


    locations = query_db("SELECT value FROM settings WHERE type = 'location' AND clinic_id = ?", [session['clinic']])


    # Loop through the items
    for item in items:
        key = (item['name'], item['category'], item['dosage'], item['form'], item['ndc'])

        # If this combination hasn't been seen before, we process it
        if key not in seen_items:
            seen_items.add(key)


            # Create a new item entry with the aggregated data
            aggregated_item = dict(item)  # Convert sqlite3.Row to a dictionary
            aggregated_item['locations'] = {}  # Initialize the locations dictionary

            # Use item['id'] as location_id, store location and quantity
            aggregated_item['locations'][item['id']] = {'location': item['location'], 'quantity': item['quantity'], 'location1': item['location1'], 'location2': item['location2'], 'location3': item['location3'], 'location4': item['location4'], 'lot_number': item['lot_number'], 'expiration_date': item['expiration_date'], 'supplier': item['supplier'], 'medication_class': item['medication_class'], 'minimum_supply': item['minimum_supply'], 'last_edit': item['last_edit'], 'removed': item['removed'], 'restock': item['restock'], 'order_quantity': item['order_quantity']}

            # New
            invalid_id_counter = -1
            for location in locations:
                location = location['value']
                if location not in [details['location'] for details in aggregated_item['locations'].values()]:
                    aggregated_item['locations'][invalid_id_counter] = {'location': location, 'quantity': 0, 'location1': "Unknown", 'location2': "Unknown", 'location3': "Unknown", 'location4': "Unknown", 'lot_number': item['lot_number'], 'expiration_date': "Unknown", 'supplier': "Unknown", 'medication_class': "Unknown", 'minimum_supply': 0, 'last_edit': item['last_edit'], 'removed': item['removed'], 'restock': 0, 'order_quantity': item['order_quantity']}
                    invalid_id_counter -= 1

            # Append the aggregated item to the result list
            aggregated_items.append(aggregated_item)

        # If this combination was already processed, we add the location and quantity to the existing entry
        else:
            # Find the item in the aggregated list
            aggregated_item = next(
                # i for i in aggregated_items if (i['name'], i['supplier'], i['category'], i['expiration_date'], i['dosage'], i['form'], i['lot_number'], i['ndc']) == key
                i for i in aggregated_items if (i['name'], i['category'], i['dosage'], i['form'], i['ndc']) == key
            )

            # Check if the location exists in the aggregated item's locations
            location_id = item['id']
            existing_location_key = next(
                (
                    key for key, loc in aggregated_item['locations'].items()
                    if 'location' in loc and 'lot_number' in loc and 'expiration_date' in loc
                    and loc['location'] == item['location']
                    and loc['lot_number'] == item['lot_number']
                    and loc['expiration_date'] == item['expiration_date']
                ),
                None
            )

            if False: #new:2-3-26
                existing_quantity = aggregated_item['locations'].get(existing_location_key, {}).get('quantity', None)
                aggregated_item['locations'][location_id] = {
                    'location': item['location'],
                    'quantity': existing_quantity + item['quantity']  # Add quantities
                }

                # Remove the old entry with the old key
                del aggregated_item['locations'][existing_location_key]


            else:
                # If the location doesn't exist, add it as a new entry
                aggregated_item['locations'][location_id] = {'location': item['location'], 'quantity': item['quantity'], 'location1': item['location1'], 'location2': item['location2'], 'location3': item['location3'], 'location4': item['location4'], 'lot_number': item['lot_number'], 'expiration_date': item['expiration_date'], 'supplier': item['supplier'], 'medication_class': item['medication_class'], 'minimum_supply': item['minimum_supply'], 'last_edit': item['last_edit'], 'removed': item['removed'], 'restock': item['restock'], 'order_quantity': item['order_quantity']}


    # NEW NEW NEW
    if sort_option == 'E':
        filtered_items = []
        for item in aggregated_items:
            # Group quantities by location
            location_totals = {}
            location_mins = {}

            for loc_id, details in item['locations'].items():
                loc_name = details['location']
                location_totals[loc_name] = location_totals.get(loc_name, 0) + details.get('quantity', 0)
                location_mins[loc_name] = details.get('minimum_supply', 0)  # Assumes all entries for the same loc have same min

            # Check if any location is understocked
            for loc_name in location_totals:
                sum_quantity = location_totals[loc_name]
                min_supply = location_mins.get(loc_name, 0)
                if sum_quantity < min_supply:
                    filtered_items.append(item)
                    break  # Only need one understocked location to include item

        aggregated_items = filtered_items


    if 'E' in selected_filters:
        filtered_items = []
        for item in aggregated_items:
            # Group quantities by location
            location_totals = {}
            location_mins = {}

            for loc_id, details in item['locations'].items():
                loc_name = details['location']
                location_totals[loc_name] = location_totals.get(loc_name, 0) + details.get('quantity', 0)
                location_mins[loc_name] = details.get('minimum_supply', 0)  # Assumes all entries for the same loc have same min

            # Check if any location is understocked
            for loc_name in location_totals:
                sum_quantity = location_totals[loc_name]
                min_supply = location_mins.get(loc_name, 0)
                if int(sum_quantity or 0) < int(min_supply or 0):
                    filtered_items.append(item)
                    break  # Only need one understocked location to include item

        aggregated_items = filtered_items


    if request.args.get('count_only') == 'true':

        total_lots = 0

        for item in aggregated_items:

            for location_id, details in item['locations'].items():

                # Must match your frontend conditions exactly

                # Skip invalid ids
                if location_id < 0:
                    continue

                # Skip removed locations
                if details.get('location') == 'REMOVED':
                    continue

                # Skip removed items (if applicable)
                if details.get('removed') == 1:
                    continue

                # Apply user-based visibility rules
                show_location = True

                if session.get('user') == 'tepati' and details.get('location') not in ['Tepati', 'Grove']:
                    show_location = False

                elif session.get('user') == 'klohc' and details.get('location') not in ['Knights Landing', 'Grove']:
                    show_location = False

                if show_location:
                    total_lots += 1

        return jsonify({'count': total_lots})
    

    # Step 2: Paginate Aggregated Items
    items_per_page = 25

    # Store total count BEFORE pagination for the filter modal
    total_aggregated_count = len(aggregated_items)

    remainder = (len(aggregated_items) % items_per_page)
    is_remainder = 0
    if remainder != 0:
        is_remainder = 2
    else:
        is_remainder = 1
    total_pages = (len(aggregated_items) // items_per_page) + is_remainder

    # Determine page slice
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page

    # Get only 30 items for the current page
    aggregated_items = aggregated_items[start_index:end_index]


    #NEW 5/11/2025
    for item in aggregated_items:
        for loc in item['locations'].values():
            date_str = loc.get('expiration_date')
            if date_str:
                try:
                    dt = datetime.strptime(date_str, "%m/%d/%Y")
                    loc['expiration_date_iso'] = dt.strftime("%Y-%m-%d")
                except ValueError:
                    loc['expiration_date_iso'] = None
            else:
                loc['expiration_date_iso'] = None

    #NEW 5/2/2025
    current_user = session.get('user')
    for item in aggregated_items:
        item['display_locations'] = prepare_location_display_data(item, itemsA, current_user)


    # Fetch locations for the dropdown (assuming you're using the 'settings' table for locations)

    clinic = session['clinic']
    site = request.args.get('location', '') or ''

    categories = query_db(
        "SELECT value FROM settings WHERE type = 'category' AND clinic_id = ?",
        [clinic]
    )
    suppliers = query_db(
        "SELECT value FROM settings WHERE type = 'supplier' AND clinic_id = ?",
        [clinic]
    )
    medication_classes = query_db(
        "SELECT value FROM settings WHERE type = 'medication_class' AND clinic_id = ?",
        [clinic]
    )
    units = query_db(
        "SELECT value FROM settings WHERE type = 'dispense_used' AND clinic_id = ?",
        [clinic]
    )
    dispenses = query_db(
        "SELECT value FROM settings WHERE type = 'dispense_as' AND clinic_id = ?",
        [clinic]
    )
    forms = query_db(
        "SELECT value FROM settings WHERE type = 'form' AND clinic_id = ?",
        [clinic]
    )

    locations1 = query_db(
        "SELECT value FROM locs WHERE type = 'location1' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )
    locations2 = query_db(
        "SELECT value FROM locs WHERE type = 'location2' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )
    locations3 = query_db(
        "SELECT value FROM locs WHERE type = 'location3' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )
    locations4 = query_db(
        "SELECT value FROM locs WHERE type = 'location4' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )

    current_date = datetime.today().strftime('%Y-%m-%d')
    # Add 30 days to the current date
    one_month_date = (datetime.today() + timedelta(days=60)).strftime('%Y-%m-%d')


    restock_count = query_db("SELECT COUNT(*) FROM items WHERE restock = 1", one=True)[0]


    return render_template('main.html', page=page, total_pages=total_pages, current_date=current_date, one_month_date=one_month_date, aggregated_items=aggregated_items, total_aggregated_count=total_aggregated_count, items=items, itemsA=itemsA, locations=locations, categories=categories, suppliers=suppliers, medication_classes=medication_classes, units=units, dispenses=dispenses, forms=forms, locations1=locations1, locations2=locations2,locations3=locations3, locations4=locations4, selected_categories=selected_categories, selected_suppliers=selected_suppliers, selected_medication_classes=selected_medication_classes, selected_locations1=selected_locations1, selected_locations2=selected_locations2, selected_locations3=selected_locations3, selected_locations4=selected_locations4, sort=sort_order, restock_count=restock_count)


#This is for the removed_inventory.html page; a copy of main.html
@app.route('/removed_inventory', methods=['GET'])
def removed_inventory():
    if not session.get('user'):
        return redirect(url_for('login'))

    search_query = request.args.get('search', '')  # Get search query from URL
    location_filter = request.args.get('location', '')  # Get selected location from URL

    #new
    location1_filter = request.args.get('location1', '')  # Get selected location from URL
    location2_filter = request.args.get('location2', '')  # Get selected location from URL
    location3_filter = request.args.get('location3', '')  # Get selected location from URL
    location4_filter = request.args.get('location4', '')  # Get selected location from URL

    category_filter = request.args.get('category', '')  # Get selected category from URL
    supplier_filter = request.args.get('supplier', '')  # Get selected supplier from URL
    medication_class_filter = request.args.get('medication_class', '')  # Get selected medication_class from URL
    last_edit_filter = request.args.get('last_edit', '')  # Get selected supplier from URL
    sort_option = request.args.get('filter', '')  # Get selected sort option from URL
    sort_order = request.args.get('sort', '') #NEW:1-11-2026


    # Base query to get all items
    query = "SELECT * FROM items WHERE 1=1"
    params = []

    # Only display items that have been removed
    query += " AND removed = ?"
    params.append(True)

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

    query += " ORDER BY name COLLATE NOCASE ASC"


    # Fetch filtered items based on the query
    items = query_db(query, params)

    clinic = session['clinic']

    locations = query_db(
        "SELECT value FROM settings WHERE type = 'location' AND clinic_id = ?",
        [clinic]
    )
    categories = query_db(
        "SELECT value FROM settings WHERE type = 'category' AND clinic_id = ?",
        [clinic]
    )
    suppliers = query_db(
        "SELECT value FROM settings WHERE type = 'supplier' AND clinic_id = ?",
        [clinic]
    )
    medication_classes = query_db(
        "SELECT value FROM settings WHERE type = 'medication_class' AND clinic_id = ?",
        [clinic]
    )
    units = query_db(
        "SELECT value FROM settings WHERE type = 'dispense_used' AND clinic_id = ?",
        [clinic]
    )
    dispenses = query_db(
        "SELECT value FROM settings WHERE type = 'dispense_as' AND clinic_id = ?",
        [clinic]
    )
    forms = query_db(
        "SELECT value FROM settings WHERE type = 'form' AND clinic_id = ?",
        [clinic]
    )

    site = request.form.get('location', '') or ''

    locations1 = query_db(
        "SELECT value FROM locs WHERE type = 'location1' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )
    locations2 = query_db(
        "SELECT value FROM locs WHERE type = 'location2' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )
    locations3 = query_db(
        "SELECT value FROM locs WHERE type = 'location3' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )
    locations4 = query_db(
        "SELECT value FROM locs WHERE type = 'location4' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )

    current_date = datetime.today().strftime('%Y-%m-%d')
    # Add 30 days to the current date
    one_month_date = (datetime.today() + timedelta(days=60)).strftime('%Y-%m-%d')
    return render_template('removed_inventory.html', current_date=current_date, one_month_date=one_month_date, items=items, locations=locations, categories=categories, suppliers=suppliers, medication_classes=medication_classes, units=units, dispenses=dispenses, forms=forms, locations1=locations1, locations2=locations2,locations3=locations3, locations4=locations4)


#This is for the restock_inventory.html page; a copy of removed_inventory.html
@app.route('/restock_inventory', methods=['GET'])
def restock_inventory():
    if not session.get('user'):
        return redirect(url_for('login'))

    search_query = request.args.get('search', '')  # Get search query from URL
    location_filter = request.args.get('location', '')  # Get selected location from URL

    #new
    location1_filter = request.args.get('location1', '')  # Get selected location from URL
    location2_filter = request.args.get('location2', '')  # Get selected location from URL
    location3_filter = request.args.get('location3', '')  # Get selected location from URL
    location4_filter = request.args.get('location4', '')  # Get selected location from URL

    category_filter = request.args.get('category', '')  # Get selected category from URL
    supplier_filter = request.args.get('supplier', '')  # Get selected supplier from URL
    medication_class_filter = request.args.get('medication_class', '')  # Get selected medication_class from URL
    last_edit_filter = request.args.get('last_edit', '')  # Get selected supplier from URL
    sort_option = request.args.get('filter', '')  # Get selected sort option from URL
    sort_order = request.args.get('sort', '') #NEW:1-11-2026


    # Base query to get all items
    query = "SELECT * FROM items WHERE 1=1"
    params = []

    # Only display items that have been restock
    query += " AND restock = ?"
    params.append(True)

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

    query += " ORDER BY name COLLATE NOCASE ASC"


    # Fetch filtered items based on the query
    items = query_db(query, params)

    clinic = session['clinic']
    site = request.form.get('location', '') or ''

    locations = query_db(
        "SELECT value FROM settings WHERE type = 'location' AND clinic_id = ?",
        [clinic]
    )
    categories = query_db(
        "SELECT value FROM settings WHERE type = 'category' AND clinic_id = ?",
        [clinic]
    )
    suppliers = query_db(
        "SELECT value FROM settings WHERE type = 'supplier' AND clinic_id = ?",
        [clinic]
    )
    medication_classes = query_db(
        "SELECT value FROM settings WHERE type = 'medication_class' AND clinic_id = ?",
        [clinic]
    )
    units = query_db(
        "SELECT value FROM settings WHERE type = 'dispense_used' AND clinic_id = ?",
        [clinic]
    )
    dispenses = query_db(
        "SELECT value FROM settings WHERE type = 'dispense_as' AND clinic_id = ?",
        [clinic]
    )
    forms = query_db(
        "SELECT value FROM settings WHERE type = 'form' AND clinic_id = ?",
        [clinic]
    )

    locations1 = query_db(
        "SELECT value FROM locs WHERE type = 'location1' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )
    locations2 = query_db(
        "SELECT value FROM locs WHERE type = 'location2' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )
    locations3 = query_db(
        "SELECT value FROM locs WHERE type = 'location3' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )
    locations4 = query_db(
        "SELECT value FROM locs WHERE type = 'location4' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )

    current_date = datetime.today().strftime('%Y-%m-%d')
    # Add 30 days to the current date
    one_month_date = (datetime.today() + timedelta(days=60)).strftime('%Y-%m-%d')
    return render_template('restock_inventory.html', current_date=current_date, one_month_date=one_month_date, items=items, locations=locations, categories=categories, suppliers=suppliers, medication_classes=medication_classes, units=units, dispenses=dispenses, forms=forms, locations1=locations1, locations2=locations2,locations3=locations3, locations4=locations4)


@app.route('/add', methods=['GET', 'POST'])
def add_item():
    search_query = request.args.get('search', '')
    location_filter = request.args.get('location', '')

    affected_items = [] #for logging purposes only

    if request.method == 'POST':
        # Basic fields
        name = request.form['name'].strip()
        aka = request.form['aka'].strip()
        status = "In Stock" # Set as default
        order_number = request.form['order_number'].strip()
        order_quantity = request.form['order_quantity'].strip()
        lot_number = request.form['lot_number'].strip() #NEW 4-20-2026
        quantity = int(request.form['quantity'])
        location = request.form.get('location', '').strip()
        location1 = request.form.get('location1', '').strip()
        location2 = request.form.get('location2', '').strip()
        location3 = request.form.get('location3', '').strip()
        location4 = request.form.get('location4', '').strip()

        #new:5-2-26
        form_data = request.form.to_dict()
        location = form_data.get("location", "")
        loc1 = form_data.get(f"location1_{location}", "")
        loc2 = form_data.get(f"location2_{location}", "")
        loc3 = form_data.get(f"location3_{location}", "")
        loc4 = form_data.get(f"location4_{location}", "")

        category = request.form['category'].strip()
        description = request.form['description'].strip()

        # Set the timezone to PST (Pacific Standard Time)
        pst_timezone = pytz.timezone('US/Pacific')

        # Get the current time in UTC and convert it to PST
        last_edit = datetime.now(pytz.utc).astimezone(pst_timezone).strftime('%Y-%m-%d %H:%M:%S')

        # Photo handling (as before)
        photo_url = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(project_root, 'static', 'uploads', filename))
                photo_url = f'uploads/{filename}'

        # Medication-specific fields (default to empty strings to avoid NULL)
        fields = ['instrument_type', 'expiration_date', 'supplier', 'medication_class', 'dosage', 'form',
                  'lot_number', 'ndc', 'dispense_used', 'dispense_as', 'unit_quantity', 'prescription_type']
        form_data = {field: request.form.get(field, '').strip() for field in fields}

        minimum_supply = request.form.get('minimum_supply', '').strip()
        if minimum_supply == '' or not minimum_supply.isdigit():
            minimum_supply = 0  # Default to 0 if the field is empty or not a valid number
        else:
            minimum_supply = int(minimum_supply)

        existing_item = query_db("""
            SELECT * FROM items
            WHERE name = ?
            AND IFNULL(aka, '') = ?
            AND IFNULL(status, '') = ?
            AND IFNULL(order_number, '') = ?
            AND IFNULL(order_quantity, '') = ?
            AND location = ?
            AND IFNULL(location1, '') = ?
            AND IFNULL(location2, '') = ?
            AND IFNULL(location3, '') = ?
            AND IFNULL(location4, '') = ?
            AND category = ?
            AND IFNULL(expiration_date, '') = ?
            AND IFNULL(supplier, '') = ?
            AND IFNULL(medication_class, '') = ?
            AND IFNULL(dosage, '') = ?
            AND IFNULL(form, '') = ?
            AND IFNULL(lot_number, '') = ?
            AND IFNULL(ndc, '') = ?
            AND IFNULL(dispense_used, '') = ?
            AND IFNULL(dispense_as, '') = ?
            AND IFNULL(unit_quantity, '') = ?
            AND IFNULL(prescription_type, '') = ?
            AND IFNULL(instrument_type, '') = ?
            AND clinic_id = ?
        """, [
            name, aka, status, order_number, order_quantity, location, 
            loc1, loc2, loc3, loc4, #new:5-2-26
            category, form_data['expiration_date'],
            form_data['supplier'], form_data['medication_class'], form_data['dosage'], form_data['form'],
            form_data['lot_number'], form_data['ndc'], form_data['dispense_used'], form_data['dispense_as'],
            form_data['unit_quantity'], form_data['prescription_type'], form_data['instrument_type'],
            session['clinic']  # <-- added clinic filter
        ], one=True)


        existing_aggregated_item_at_location = query_db("""
            SELECT * FROM items
            WHERE name = ?
            AND location = ?
            AND IFNULL(location1, '') = ?
            AND IFNULL(location2, '') = ?
            AND IFNULL(location3, '') = ?
            AND IFNULL(location4, '') = ?
            AND category = ?
            AND IFNULL(dosage, '') = ?
            AND IFNULL(form, '') = ?
            AND IFNULL(ndc, '') = ?
            AND clinic_id = ?
        """, [
            name,
            location,
            loc1, #new:5-2-26
            loc2, #new:5-2-26
            loc3, #new:5-2-26
            loc4, #new:5-2-26
            category,
            form_data['dosage'],
            form_data['form'],
            form_data['ndc'],
            session['clinic']  # <-- added clinic filter
        ])


        if existing_item:
            min_sup = minimum_supply if minimum_supply != 0 else existing_item['minimum_supply']
            # Update the quantity if item exists, scoped to the current clinic
            query_db("""
                UPDATE items
                SET quantity = quantity + ?,
                    minimum_supply = ?,
                    last_edit = ?
                WHERE id = ? AND clinic_id = ?
            """, [
                quantity,
                min_sup,
                last_edit,
                existing_item['id'],
                session['clinic']  # <-- added clinic filter
            ])
            affected_items.append({"id": '', "quantity": quantity})


        elif existing_aggregated_item_at_location:
            min_sup = minimum_supply if minimum_supply != 0 else existing_aggregated_item_at_location[0]['minimum_supply']

            # Insert new item scoped to the current clinic
            query_db("""
                INSERT INTO items (name, aka, status, quantity, location, location1, location2, location3, location4,
                                category, description, photo_url, instrument_type, expiration_date, supplier,
                                medication_class, order_number, order_quantity, dosage, form, lot_number, ndc, dispense_used,
                                dispense_as, unit_quantity, prescription_type, minimum_supply, last_edit, clinic_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                name, aka, status, quantity,
                location,
                existing_aggregated_item_at_location[0]['location1'],
                existing_aggregated_item_at_location[0]['location2'],
                existing_aggregated_item_at_location[0]['location3'],
                existing_aggregated_item_at_location[0]['location4'],
                category, description, photo_url, form_data['instrument_type'],
                form_data['expiration_date'], form_data['supplier'], form_data['medication_class'],
                order_number, order_quantity, form_data['dosage'], form_data['form'], form_data['lot_number'], form_data['ndc'],
                form_data['dispense_used'], form_data['dispense_as'], form_data['unit_quantity'],
                form_data['prescription_type'], min_sup, last_edit,
                session['clinic']  # <-- added clinic_id for INSERT
            ])
            new_id = query_db("SELECT last_insert_rowid() AS id", one=True)['id']
            affected_items.append({"id": f'', "quantity": quantity})

            # Update minimum_supply for existing items, scoped to the current clinic
            for item in existing_aggregated_item_at_location:
                if minimum_supply != 0 and item['minimum_supply'] != minimum_supply:
                    query_db("""
                        UPDATE items
                        SET minimum_supply = ?, last_edit = ?
                        WHERE id = ? AND clinic_id = ?
                    """, [
                        minimum_supply, last_edit,
                        item['id'],
                        session['clinic']  # <-- added clinic_id for UPDATE
                    ])
                
                #NEW 4-20-2026
                else:
                    if lot_number == item['lot_number']:
                        # Always update last_edit
                        query_db("""
                            UPDATE items
                            SET last_edit = ?
                            WHERE id = ? AND clinic_id = ?
                        """, [
                            last_edit,
                            item['id'],
                            session['clinic']
                        ])


        else:

            # New: 1-19-2026
            existing_aggregated_item = query_db("""
                SELECT * FROM items
                WHERE name = ?
                AND category = ?
                AND IFNULL(dosage, '') = ?
                AND IFNULL(form, '') = ?
                AND IFNULL(ndc, '') = ?
                AND clinic_id = ?
            """, [
                name,
                category,
                form_data['dosage'],
                form_data['form'],
                form_data['ndc'],
                session['clinic']  # <-- added clinic filter
            ])

            existing_photo_url = photo_url  # default fallback

            existing_photo_url = photo_url  # default fallback


            if existing_aggregated_item:

                matching_photo_urls = []

                for idx, item in enumerate(existing_aggregated_item):

                    photo_url_value = item['photo_url']  # correct for sqlite3.Row

                    if photo_url_value:
                        matching_photo_urls.append(photo_url_value)
                    else:
                        pass


                if matching_photo_urls:
                    existing_photo_url = matching_photo_urls[0]
                else:
                    pass
            else:
                pass


            # Insert new item scoped to the current clinic
            query_db("""
                INSERT INTO items (name, aka, status, quantity, location, location1, location2, location3, location4,
                                category, description, photo_url, instrument_type, expiration_date, supplier,
                                medication_class, order_number, order_quantity, dosage, form, lot_number, ndc, dispense_used,
                                dispense_as, unit_quantity, prescription_type, minimum_supply, last_edit, clinic_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                name, aka, status, quantity,
                location, location1, location2, location3, location4,
                category, description, existing_photo_url, form_data['instrument_type'],
                form_data['expiration_date'], form_data['supplier'], form_data['medication_class'],
                order_number, order_quantity, form_data['dosage'], form_data['form'], form_data['lot_number'], form_data['ndc'],
                form_data['dispense_used'], form_data['dispense_as'], form_data['unit_quantity'],
                form_data['prescription_type'], minimum_supply, last_edit,
                session['clinic']  # <-- added clinic_id for INSERT
            ])
            new_id = ''
            affected_items.append({"id": new_id, "quantity": quantity})


        flash('Item added successfully.', 'success')


        # Log items added
        def add_log_entries(messages):
            for entry in affected_items:
                messages.append({
                    "category": "log",
                    "ts": datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M:%S"),
                    "user": session['user'] if session.get('clinic') == 'inventory' else session['clinic'],
                    "username": session["username"],
                    "action": "added",
                    "name": name,
                    "amount": str(entry['quantity']),
                    "notes": str(entry['id'])
                })

        update_messages_safely(add_log_entries)


        return jsonify({
            "success": True,
            "redirect_url": url_for('main_page', search=search_query, location=location_filter)
        })


    # Extract query parameters for prefill
    prefill_values = {
        'name': request.args.get('name', ''),
        'aka': request.args.get('aka', ''),
        'status': request.args.get('status', ''),
        'quantity': request.args.get('quantity', ''),
        'location': request.args.get('location', ''),
        'location1': request.args.get('location1', ''),
        'location2': request.args.get('location2', ''),
        'location3': request.args.get('location3', ''),
        'location4': request.args.get('location4', ''),
        'category': request.args.get('category', ''),
        'description': request.args.get('description', ''),
        'instrument_type': request.args.get('instrument_type', ''),
        'expiration_date': request.args.get('expiration_date', ''),
        'supplier': request.args.get('supplier', ''),
        'medication_class': request.args.get('medication_class', ''),
        'order_number': request.args.get('order_number', ''),
        'order_quantity': request.args.get('order_quantity', ''),
        'dosage': request.args.get('dosage', ''),
        'form': request.args.get('form', ''),
        'lot_number': request.args.get('lot_number', ''),
        'ndc': request.args.get('ndc', ''),
        'dispense_used': request.args.get('dispense_used', ''),
        'dispense_as': request.args.get('dispense_as', ''),
        'unit_quantity': request.args.get('unit_quantity', ''),
        'prescription_type': request.args.get('prescription_type', ''),
        'minimum_supply': request.args.get('minimum_supply', ''),
        'photo_url': request.args.get('photo_url', ''),
        'last_edit': request.args.get('last_edit', ''),
        'removed': request.args.get('removed', '')
    }

    # Add per-location minimum_supply values from query parameters
    # This allows each location to have its own minimum_supply prefilled
    clinic = session['clinic']
    site = request.form.get('location', '') or ''
    
    locations = query_db(
        "SELECT value FROM settings WHERE type = 'location' AND clinic_id = ?",
        [clinic]
    )
    for location in locations:
        location_name = location[0].replace(' ', '_')
        param_name = f'minimum_supply_{location_name}'
        prefill_values[param_name] = request.args.get(param_name, '')


    categories = query_db(
        "SELECT value FROM settings WHERE type = 'category' AND clinic_id = ?",
        [clinic]
    )
    suppliers = query_db(
        "SELECT value FROM settings WHERE type = 'supplier' AND clinic_id = ?",
        [clinic]
    )
    medication_classes = query_db(
        "SELECT value FROM settings WHERE type = 'medication_class' AND clinic_id = ?",
        [clinic]
    )
    units = query_db(
        "SELECT value FROM settings WHERE type = 'dispense_used' AND clinic_id = ?",
        [clinic]
    )
    dispenses = query_db(
        "SELECT value FROM settings WHERE type = 'dispense_as' AND clinic_id = ?",
        [clinic]
    )
    forms = query_db(
        "SELECT value FROM settings WHERE type = 'form' AND clinic_id = ?",
        [clinic]
    )

    locations1 = query_db(
        "SELECT value FROM locs WHERE type = 'location1' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )
    locations2 = query_db(
        "SELECT value FROM locs WHERE type = 'location2' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )
    locations3 = query_db(
        "SELECT value FROM locs WHERE type = 'location3' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )
    locations4 = query_db(
        "SELECT value FROM locs WHERE type = 'location4' AND site = ? AND clinic_id = ?",
        [site, clinic]
    )


    query = "SELECT * FROM items WHERE 1=1" 
    params = [] 
    query += " AND clinic_id = ?" 
    params.append(session['clinic']) 
    items = query_db(query, params)

    prefill_location1 = {}

    for item in items:
        if (
            item['name'] == request.args.get('name')
            and item['category'] == request.args.get('category')
            and item['lot_number'] == request.args.get('lot_number')
        ):
            # Each location may have a different location1
            prefill_location1[item['location']] = item['location1']

    return render_template('add_item.html', items=items, prefill_location1=prefill_location1, prefill_values=prefill_values, locations=locations, categories=categories, suppliers=suppliers, medication_classes=medication_classes, units=units, dispenses=dispenses, forms=forms, locations1=locations1, locations2=locations2,locations3=locations3, locations4=locations4, search=search_query, location=location_filter)


@app.route('/get_locations', methods=['GET'])
def get_locations():


    location = request.args.get('location', '')
    clinic = session['clinic']


    # Fetch items to get prefill values for the location
    query = "SELECT * FROM items WHERE 1=1"
    params = []
    query += " AND clinic_id = ?"
    params.append(clinic)
    
    
    items = query_db(query, params)
    
    
    # Initialize the prefill location dictionaries
    prefill_location1 = {}
    prefill_location2 = {}
    prefill_location3 = {}
    prefill_location4 = {}

    # Populate prefill values for each location based on matching name, category, and lot_number
    for item in items:
        
        # Extract the specific fields you're comparing to request args
        item_name = item['name']
        item_category = item['category']
        item_lot_number = item['lot_number']
        item_location = item['location']
        item_location1 = item['location1']
        item_location2 = item['location2']
        item_location3 = item['location3']
        item_location4 = item['location4']
        

        # Print the exact criteria the item must match
        request_name = request.args.get('name')
        request_category = request.args.get('category')
        request_lot_number = request.args.get('lot_number')


        # Check if the current item matches the given name, category, and lot_number from the request args
        if (
            item_name == request_name and
            item_category == request_category and
            item_lot_number == request_lot_number
        ):

            # Assign values to prefill dictionaries
            prefill_location1[item_location] = item_location1
            prefill_location2[item_location] = item_location2
            prefill_location3[item_location] = item_location3
            prefill_location4[item_location] = item_location4

        else:
            pass
            

    # Query locations based on the location type (location1, location2, etc.)
    query1 = "SELECT value FROM locs WHERE type = 'location1' AND site = ? AND clinic_id = ? ORDER BY value COLLATE NOCASE ASC"
    query2 = "SELECT value FROM locs WHERE type = 'location2' AND site = ? AND clinic_id = ? ORDER BY value COLLATE NOCASE ASC"
    query3 = "SELECT value FROM locs WHERE type = 'location3' AND site = ? AND clinic_id = ? ORDER BY value COLLATE NOCASE ASC"
    query4 = "SELECT value FROM locs WHERE type = 'location4' AND site = ? AND clinic_id = ? ORDER BY value COLLATE NOCASE ASC"
    
    locations1 = query_db(query1, [location, clinic])
    locations2 = query_db(query2, [location, clinic])
    locations3 = query_db(query3, [location, clinic])
    locations4 = query_db(query4, [location, clinic])


    # Return JSON with locations and prefill values
    response_data = {
        'locations1': [loc[0] for loc in locations1],
        'locations2': [loc[0] for loc in locations2],
        'locations3': [loc[0] for loc in locations3],
        'locations4': [loc[0] for loc in locations4],
        'prefill_location1': prefill_location1,
        'prefill_location2': prefill_location2,
        'prefill_location3': prefill_location3,
        'prefill_location4': prefill_location4
    }

    # Log the final response being sent
    print(f"Response data: {response_data}")

    return jsonify(response_data)


@app.route('/mark_removed/<int:item_id>', methods=['POST'])
def mark_removed(item_id):
    item = query_db(
        "SELECT id, removed, name, category, dosage, form, ndc, quantity FROM items WHERE id = ? AND clinic_id = ?",
        [item_id, session['clinic']],
        one=True
    )

    if item:

        # NEW 10/24/25
        # If the item is currently removed (removed == 1), set 'delisted' to 0 for matching items
        if item['removed'] == 1:
            print('If the item is currently removed (removed == 1), set delisted to 0 for matching items')
            query_db("""
                UPDATE items
                SET delisted = 0
                WHERE name = ? AND category = ? 
                    AND dosage = ? AND form = ? AND ndc = ? 
                    AND clinic_id = ?
            """, [
                item['name'], item['category'],
                item['dosage'], item['form'], item['ndc'],
                session['clinic']  # <-- restrict to current clinic
            ])
            

        # Toggle the 'removed' status
        new_removed_status = 0 if item['removed'] == 1 else 1
        query_db(
            "UPDATE items SET removed = ? WHERE id = ? AND clinic_id = ?",
            [new_removed_status, item_id, session['clinic']]
        )

        # Mark In Stock to Removed or Returned
        new_status = "In Stock" if item['removed'] == 1 else "Removed"
        query_db(
            "UPDATE items SET status = ? WHERE id = ? AND clinic_id = ?",
            [new_status, item_id, session['clinic']]
        )


        if new_removed_status == 1:
            # log items deleted
            messages = load_messages()

            messages.append({
                "category": "log",
                "ts": datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M:%S"),
                # "user": f"{session['user']}",
                "user": session['user'] if session.get('clinic') == 'inventory' else session['clinic'],
                "username": session["username"],
                "action": f"removed",
                "name": f"{item['name']}",
                "amount": f"{item['quantity']}",
                "notes": f""
            })
            save_messages(messages)


    # Get the current URL hash (scroll position) from the form data using the unique name for each form
    current_hash = request.form.get(f'current_hash_{item_id}', '')

    # Print for debugging (optional)
    print('Captured hash from form:', current_hash)  # Will print in the server terminal/log

    # Get the referrer URL and append the hash to it
    referrer_url = request.referrer
    if current_hash:
        referrer_url = f"{referrer_url}#{current_hash}"


    # Redirect to the same page with the hash (scroll position)
    return redirect(referrer_url)


@app.route('/mark_restock/<int:item_id>', methods=['POST'])
def mark_restock(item_id):
    item = query_db(
        "SELECT id, restock FROM items WHERE id = ? AND clinic_id = ?",
        [item_id, session['clinic']],
        one=True
    )

    if item:
        # Toggle the 'restock' status
        new_restock_status = 0 if item['restock'] == 1 else 1
        query_db(
            "UPDATE items SET restock = ? WHERE id = ? AND clinic_id = ?",
            [new_restock_status, item_id, session['clinic']]
        )

        # Mark In Stock to Restock Requested or Returned
        new_status = "In Stock" if item['restock'] == 1 else "Restock Requested"
        query_db(
            "UPDATE items SET status = ? WHERE id = ? AND clinic_id = ?",
            [new_status, item_id, session['clinic']]
        )


    # Get the current URL hash (scroll position) from the form data using the unique name for each form
    current_hash = request.form.get(f'current_hash_{item_id}', '')

    # Print for debugging (optional)
    print('Captured hash from form:', current_hash)  # Will print in the server terminal/log

    # Get the referrer URL and append the hash to it
    referrer_url = request.referrer
    if current_hash:
        referrer_url = f"{referrer_url}#{current_hash}"

    # Redirect to the same page with the hash (scroll position)
    return redirect(referrer_url)


@app.route('/mark_removed_from_all_sites/<int:item_id>', methods=['POST'])
def mark_removed_from_all_sites(item_id):
    item = query_db(
        """
        SELECT id, name, supplier, category, expiration_date, order_number,
            dosage, form, lot_number, ndc, removed
        FROM items
        WHERE id = ? AND clinic_id = ?
        """,
        [item_id, session['clinic']],
        one=True
    )


    if item:
        # Toggle the 'removed' and return status
        new_removed_status = 0 if item['removed'] == 1 else 1
        new_status = "In Stock" if item['removed'] == 1 else "Removed"

        # Update all matching items based on the selected attributes
        # query_db(
        #     """
        #     UPDATE items
        #     SET removed = ?, status = ?
        #     WHERE name = ? AND supplier = ? AND category = ? AND expiration_date = ?
        #       AND order_number = ? AND dosage = ? AND form = ? AND lot_number = ? AND ndc = ?
        #     """,
        #     [
        #         new_removed_status, new_status, item['name'], item['supplier'],
        #         item['category'], item['expiration_date'], item['order_number'],
        #         item['dosage'], item['form'], item['lot_number'], item['ndc']
        #     ]
        # )

        # Update all matching items based on the selected attributes
        # query_db(
        #     """
        #     UPDATE items
        #     SET removed = ?, status = ?
        #     WHERE name = ? AND supplier = ? AND medication_class = ? AND category = ? AND expiration_date = ?
        #       AND dosage = ? AND form = ? AND lot_number = ? AND ndc = ?
        #     """,
        #     [
        #         new_removed_status, new_status, item['name'], item['supplier'], item['medication_class'],
        #         item['category'], item['expiration_date'],
        #         item['dosage'], item['form'], item['lot_number'], item['ndc']
        #     ]
        # )
        query_db(
            """
            UPDATE items
            SET removed = ?, status = ?
            WHERE name = ? AND supplier = ? AND medication_class = ? AND category = ? AND expiration_date = ?
            AND dosage = ? AND form = ? AND lot_number = ? AND ndc = ?
            AND clinic_id = ?
            """,
            [
                new_removed_status, new_status,
                item['name'], item['supplier'], item['medication_class'],
                item['category'], item['expiration_date'],
                item['dosage'], item['form'], item['lot_number'], item['ndc'],
                session['clinic']  # <-- restrict to current clinic
            ]
        )

    # Get the current URL hash (scroll position) from the form data using the unique name for each form
    current_hash = request.form.get(f'current_hash_{item_id}', '')

    # Print for debugging (optional)
    print('Captured hash from form:', current_hash)  # Will print in the server terminal/log

    # Get the referrer URL and append the hash to it
    referrer_url = request.referrer
    if current_hash:
        referrer_url = f"{referrer_url}#{current_hash}"

    # Redirect to the same page with the hash (scroll position)
    return redirect(referrer_url)


@app.route('/save_scroll_position', methods=['POST'])
def save_scroll_position():
    # Attempt to parse the JSON data from the body
    data = request.get_json()

    if data is None:
        return jsonify({'error': 'No JSON data provided'}), 400

    # Extract the 'current_hash' field from the JSON data
    current_hash = data.get('current_hash')

    if not current_hash:
        return jsonify({'error': 'No current_hash field in JSON'}), 400

    # Save to session or perform other logic
    session['current_hash'] = current_hash

    return jsonify({'message': 'Scroll position saved successfully', 'current_hash': current_hash}), 200


@app.route('/view/<int:item_id>', methods=['GET', 'POST'])
def view_item(item_id):

    item = query_db(
        "SELECT * FROM items WHERE id = ? AND clinic_id = ?",
        [item_id, session['clinic']],
        one=True
    )

    search_query = request.args.get('search', '')  # Get search query from URL
    location_filter = request.args.get('location', '')  # Get selected location from URL

    current_hash = session.get('current_hash', None)

    if request.method == 'POST':
        # Basic fields
        name = request.form['name']
        aka = request.form['aka']
        status = request.form['status']
        order_number = request.form['order_number']
        order_quantity = request.form['order_quantity']
        quantity = request.form['quantity']
        location = request.form['location']
        location1 = request.form['location1']
        location2 = request.form['location2']
        location3 = request.form['location3']
        location4 = request.form['location4']
        category = request.form['category']
        description = request.form['description']
        minimum_supply = request.form['minimum_supply']  # New field for minimum supply
        last_edit = request.form['last_edit']

        photo_url = None  # Default to None if no photo is uploaded
        # Handle file upload (if any)
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                print(f"Saving file: {filename}")  # Debugging
                file.save(os.path.join(project_root, 'static', 'uploads', filename))
                photo_url = f'uploads/{filename}'  # Path relative to static folder
            else:
                print("File not allowed or no file provided.")
        else:
            print("No file uploaded.")

        # New fields (medication/surgical instrument specific)
        instrument_type = request.form.get('instrument_type', None)
        expiration_date = request.form.get('expiration_date', None)
        supplier = request.form.get('supplier', None)
        medication_class = request.form.get('medication_class', None)
        dosage = request.form.get('dosage', None)
        form = request.form.get('form', None)
        lot_number = request.form.get('lot_number', None)
        ndc = request.form.get('ndc', None)
        dispense_used = request.form.get('dispense_used', None)
        dispense_as = request.form.get('dispense_as', None)
        unit_quantity = request.form.get('unit_quantity', None)
        prescription_type = request.form.get('prescription_type', None)

        query_db("""
            UPDATE items SET
                name = ?, aka = ?, status = ?, order_number = ?, order_quantity = ?, quantity = ?, location = ?, location1 = ?, location2 = ?, location3 = ?, location4 = ?, 
                category = ?, description = ?, photo_url = ?, instrument_type = ?, expiration_date = ?, supplier = ?, medication_class = ?, dosage = ?, form = ?,
                lot_number = ?, ndc = ?, dispense_used = ?, dispense_as = ?, unit_quantity = ?, prescription_type = ?, minimum_supply = ?, last_edit = ?
            WHERE id = ? AND clinic_id = ?
        """, [
            name, aka, status, order_number, order_quantity, quantity, location, location1, location2, location3, location4,
            category, description, photo_url, instrument_type, expiration_date, supplier, medication_class,
            dosage, form, lot_number, ndc, dispense_used, dispense_as, unit_quantity, prescription_type,
            minimum_supply, last_edit, item_id, session['clinic']  # <-- restrict to current clinic
        ])


        # After updating, redirect back to the main page with the search and location query parameters

        return redirect(url_for('main_page', search=search_query, location=location_filter))

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

    locations1 = query_db(
        "SELECT value FROM locs WHERE type = 'location1' AND site = ? AND clinic_id = ?",
        [request.form.get('location', '') or '', session['clinic']]
    )
    locations2 = query_db(
        "SELECT value FROM locs WHERE type = 'location2' AND site = ? AND clinic_id = ?",
        [request.form.get('location', '') or '', session['clinic']]
    )
    locations3 = query_db(
        "SELECT value FROM locs WHERE type = 'location3' AND site = ? AND clinic_id = ?",
        [request.form.get('location', '') or '', session['clinic']]
    )
    locations4 = query_db(
        "SELECT value FROM locs WHERE type = 'location4' AND site = ? AND clinic_id = ?",
        [request.form.get('location', '') or '', session['clinic']]
    )

    current_date = datetime.today().strftime('%Y-%m-%d')
    one_month_date = (datetime.today() + timedelta(days=60)).strftime('%Y-%m-%d')
    return render_template('view_item.html', item=item, locations=locations, current_date=current_date, one_month_date=one_month_date, current_hash=current_hash, categories=categories, suppliers=suppliers, medication_classes=medication_classes, units=units, dispenses=dispenses, forms=forms, locations1=locations1, locations2=locations2,locations3=locations3, locations4=locations4, search=search_query, location=location_filter)


@app.route('/remove_photo/<int:item_id>', methods=['POST'])
def remove_photo(item_id):
    print(f"Attempting to remove photo for item with ID: {item_id}")

    # Fetch the item details from the database
    item = query_db(
        "SELECT photo_url FROM items WHERE id = ? AND clinic_id = ?",
        [item_id, session['clinic']],
        one=True
    )

    # Check if item exists and has a photo URL (use dictionary-style access)
    if item:
        print(f"Item found: {item}")
        if item['photo_url']:  # Direct access using the key
            photo_url = item['photo_url']
            print(f"Found photo URL: {photo_url}")
            
            # Check if this photo is used by other items in the same clinic
            other_items_with_photo = query_db(
                "SELECT COUNT(*) FROM items WHERE photo_url = ? AND clinic_id = ? AND id != ?",
                [photo_url, session['clinic'], item_id],
                one=True
            )
            print(f"Other items with the same photo: {other_items_with_photo[0]}")
            
            # If no other item uses this photo, we can delete it from the server
            if other_items_with_photo[0] == 0:
                photo_path = os.path.join(project_root, 'static', photo_url)
                print(f"Checking if photo exists at: {photo_path}")
                if os.path.exists(photo_path):
                    try:
                        os.remove(photo_path)
                        print(f"Deleted photo: {photo_path}")  # Debugging log
                    except Exception as e:
                        print(f"Error deleting photo: {e}")
                else:
                    print(f"Photo not found at: {photo_path}")
            else:
                print("Photo is still used by other items, not deleting.")

            # Remove the photo URL from the database for this item only
            print(f"Updating database to remove photo URL for item ID: {item_id}")
            query_db(
                "UPDATE items SET photo_url = NULL WHERE id = ? AND clinic_id = ?",
                [item_id, session['clinic']]
            )
            print(f"Database updated: photo_url set to NULL for item ID: {item_id}")
        else:
            print("No photo URL found for item, nothing to remove.")
    else:
        print(f"Item with ID {item_id} not found.")

    return "Photo removed", 200

@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    print(f"Attempting to delete item with ID: {item_id}")
    item = query_db(
        "SELECT name, quantity, location, removed, photo_url FROM items WHERE id = ? AND clinic_id = ?",
        [item_id, session['clinic']],
        one=True
    )

    # log items deleted
    messages = load_messages()

    removed = item['removed']
    print("LINE 3310 removed: ", removed)
    if removed:
        note = ''
    else:
        item_location = "KL" if item['location'] == "Knights Landing" else item['location']
        note = f"from {item_location}"

    messages.append({
        "category": "log",
        "ts": datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M:%S"),
        # "user": f"{session['user']}",
        "user": session['user'] if session.get('clinic') == 'inventory' else session['clinic'],
        "username": session["username"],
        "action": f"deleted",
        "name": f"{item['name']}",
        "amount": f"{item['quantity']}",
        "notes": f"{note}"
    })
    save_messages(messages)

    if item and item['photo_url']:
        photo_url = item['photo_url']
        # Check if this photo is used by other items
        other_items_with_photo = query_db(
            "SELECT COUNT(*) FROM items WHERE photo_url = ? AND clinic_id = ? AND id != ?",
            [photo_url, session['clinic'], item_id],
            one=True
        )
        
        # If no other item uses this photo, we can delete it
        if other_items_with_photo[0] == 0:
            photo_path = os.path.join(project_root, 'static', photo_url)
            if os.path.exists(photo_path):
                os.remove(photo_path)
                print(f"Deleted photo: {photo_path}")  # Debugging log

    # Delete the item from the database
    # query_db("DELETE FROM items WHERE id = ?", [item_id])
    query_db(
        "DELETE FROM items WHERE id = ? AND clinic_id = ?",
        [item_id, session['clinic']]
    )


    # NEW: 2-05-2026
    # Get the current URL hash (scroll position) from the form data using the unique name for each form
    current_hash = request.form.get(f'current_hash_{item_id}', '')

    # Print for debugging (optional)
    print('Captured hash from form:', current_hash)  # Will print in the server terminal/log

    # Get the referrer URL and append the hash to it
    referrer_url = request.referrer
    if current_hash:
        referrer_url = f"{referrer_url}#{current_hash}"

    # Redirect to the same page with the hash (scroll position)
    return redirect(referrer_url)


@app.route('/delete_item_from_all_sites/<int:item_id>')
def delete_item_from_all_sites(item_id):
    item = query_db("""
        SELECT name, category, dosage, form, ndc,
            COALESCE(removed, 0) AS removed, photo_url
        FROM items
        WHERE id = ? AND clinic_id = ?
    """, [item_id, session['clinic']], one=True)


    if not item:
        # If the item doesn't exist, redirect back to the main page
        return redirect(url_for('main_page'))

    items_to_delete = query_db("""
        SELECT id, photo_url
        FROM items
        WHERE name = ? AND category = ?
            AND dosage = ? AND form = ? AND ndc = ?
            AND (removed = ? OR removed IS NULL)
            AND clinic_id = ?
    """, [item['name'], item['category'],
        item['dosage'], item['form'], item['ndc'], item['removed'],
        session['clinic']])


    for item_to_delete in items_to_delete:
        if item_to_delete['photo_url']:
            photo_url = item_to_delete['photo_url']
            
            # Check if the photo is used by any other items
            other_items_with_photo = query_db(
                "SELECT COUNT(*) FROM items WHERE photo_url = ? AND clinic_id = ? AND id != ?",
                [photo_url, session['clinic'], item_to_delete['id']],
                one=True
            )
            
            # If no other item uses this photo, we can delete it
            if other_items_with_photo[0] == 0:
                photo_path = os.path.join(project_root, 'static', photo_url)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
                    print(f"Deleted photo: {photo_path}")  # Debugging log

    # Delete all items with the same name, category, etc.
    # query_db("""
    #     DELETE FROM items
    #     WHERE name = ? AND category = ?
    #           AND dosage = ? AND form = ? AND ndc = ?
    #           AND (removed = ? OR removed IS NULL)
    # """, [item['name'], item['category'],
    #       item['dosage'], item['form'], item['ndc'], item['removed']])
    query_db("""
        DELETE FROM items
        WHERE name = ? AND category = ?
            AND dosage = ? AND form = ? AND ndc = ?
            AND (removed = ? OR removed IS NULL)
            AND clinic_id = ?
    """, [item['name'], item['category'],
        item['dosage'], item['form'], item['ndc'], item['removed'],
        session['clinic']])

    # Get the search and location filters from the URL
    search_query = request.args.get('search', '')  # Get search query from URL
    location_filter = request.args.get('location', '')  # Get selected location from URL

    # Redirect back to the main page with filters applied
    return redirect(url_for('main_page', search=search_query, location=location_filter))


# NEW: 2-08-2026
@app.route('/delist/<int:item_id>', methods=['POST', 'GET'])
def delist(item_id):
    # Fetch the item's details
    item = query_db("""
        SELECT name, category, dosage, form, ndc
        FROM items
        WHERE id = ? AND clinic_id = ?
    """, [item_id, session['clinic']], one=True)

    if not item:
        return redirect(url_for('main_page'))

    # Find items that will actually change (removed IS NULL or removed != 1)
    to_log = query_db("""
        SELECT id, name, quantity
        FROM items
        WHERE name = ? AND category = ? AND dosage = ? AND form = ? AND ndc = ?
            AND clinic_id = ? AND (removed IS NULL OR removed != 1)
    """, [item['name'], item['category'], item['dosage'], item['form'], item['ndc'], session['clinic']])

    # Update all matching items (same as original behavior)
    query_db("""
        UPDATE items
        SET delisted = 1, removed = 1, status = 'Removed'
        WHERE name = ? AND category = ? AND dosage = ? AND form = ? AND ndc = ?
            AND clinic_id = ?
    """, [item['name'], item['category'], item['dosage'], item['form'], item['ndc'], session['clinic']])

    # Load messages
    messages = load_messages()

    # Log only the items that were actually changed
    for itm in to_log:
        messages.append({
            "category": "log",
            "ts": datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M:%S"),
            "user": session['user'] if session.get('clinic') == 'inventory' else session['clinic'],
            "username": session["username"],
            "action": "delisted",
            "name": itm['name'],
            "amount": itm['quantity'],
            "notes": ""
        })

    # Save updated messages
    save_messages(messages)

    # Preserve scroll position/hash
    current_hash = request.form.get(f'current_hash_{item_id}', '')
    referrer_url = request.referrer
    if current_hash:
        referrer_url = f"{referrer_url}#{current_hash}"

    return redirect(referrer_url)



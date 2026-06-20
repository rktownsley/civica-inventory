from app_context import *

@app.route("/login", methods=["GET", "POST"])
def login():
    print("Login route accessed")  # Check if route is hit
    view = request.args.get("view", "login")  # Default to "login" if no view parameter is provided

    # For the POST method, handle login or signup logic based on view
    if request.method == "POST":
        if view == "login":
            print("POST request for login received")
            email = request.form.get("email")
            password = request.form.get("password")
            print(f"Received email: {email}, password: {password}")

            # Load users
            try:
                with open(USER_FILE, "r") as f:
                    users = json.load(f)
                print(f"Loaded {len(users)} users from {USER_FILE}")
            except Exception as e:
                print(f"Error loading user file: {e}")
                flash("Internal server error loading users.", "error")
                return redirect(url_for("login", view=view))

            # Find user
            user = next((u for u in users if u["email"] == email and u["password"] == password), None)
            if user:
                print(f"User found: {user}")
                session["username"] = user["email"]
                session["user"] = user["role"]
                session["clinic"] = user["clinic_affiliation"]

                session['supervisor'] = False
                if session['user'] == 'supervisor':
                    session['user'] = 'admin'
                    session['supervisor'] = True

                flash(f"Welcome back, {user['first_name']}!", "success")
                
                try:
                    print("Setting clinic database...")
                    set_clinic_database()
                    print("Initializing database...")
                    init_db()
                    print("Redirecting to main_page...")
                except Exception as e:
                    print(f"Error initializing database: {e}")
                    flash("Internal server error setting up database.", "error")
                    return redirect(url_for("login", view=view))

                return redirect(url_for('main_page'))
            else:
                print("User not found or password incorrect")
                flash("Invalid email or password.", "error")
                return redirect(url_for("login", view=view))

        elif view == "register":
            print("POST request for signup received")
            username = request.form.get("username")
            password = request.form.get("password")
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")
            email = request.form.get("email")
            role = request.form.get("role")
            clinic_code = request.form.get("clinic_affiliation").strip().upper()  # user-entered code
            admin_code = request.form.get("admin_code").strip().upper()  # user-entered code

            if role == "admin" and admin_code != "12345":
                flash(f"Invalid Supervisor Code", "error")


            # Load clinic code -> name map
            try:
                with open(CLINIC_FILE, "r") as f:
                    clinics = json.load(f)
            except Exception as e:
                flash(f"Error loading clinics: {e}", "error")
                return redirect(url_for("login", view=view))

            # Match code to clinic name
            clinic_name = clinics.get(clinic_code)
            if not clinic_name:
                flash("Invalid clinic code. Please try again.", "error")
                return redirect(url_for("login", view=view))

            # Load or initialize user list
            try:
                with open(USER_FILE, "r") as f:
                    users = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                users = []

            # Check if username already exists
            if any(u["username"] == username for u in users):
                flash("Username already exists. Please choose another.", "error")
                return redirect(url_for("login", view=view))

            # Auto-adjust viewer roles based on clinic code
            if role == "viewer":
                if clinic_code.upper() == "TEPATI":
                    role = "tepati"
                elif clinic_code.upper() == "KLOHC":
                    role = "klohc"

            # Create new user record
            new_user = {
                "username": username,
                "password": password,  # (plain text for now)
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "role": role,
                "clinic_code": clinic_code,           # store code
                "clinic_affiliation": clinic_name     # store name
            }

            # Save user
            users.append(new_user)
            with open(USER_FILE, "w") as f:
                json.dump(users, f, indent=4)

            flash("Signup successful! Please log in.", "success")
            return redirect(url_for("login", view="login"))  # Redirect to login page after successful signup

    print("GET request - rendering login page")
    
    # Load clinic codes for signup page
    if view == "register":
        try:
            with open(CLINIC_FILE, "r") as f:
                clinics = json.load(f)
        except Exception as e:
            flash(f"Error loading clinics: {e}", "error")
            return redirect(url_for("login", view="login"))

        # Pass clinic_codes to the template for registration
        return render_template("login.html", view=view, clinic_codes=clinics)

    # Default to login page if not in register view
    return render_template("login.html", view=view)


@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove the user from the session
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))


SECRET_KEY = app.secret_key

@app.route("/auth")
def auth():
    token = request.args.get("token")
    if not token:
        return "Missing token", 400

    token = unquote(token)  # fix URL encoding

    try:
        # Decode the JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        # **Print the fully decoded JWT payload**
        print("DEBUG: Decoded JWT payload:", payload)

        # Save user information in session

        if "clinic_name" in payload:
            session['clinic'] = payload["clinic_name"]
        elif "clinic_affiliation" in payload:
            session['clinic'] = payload["clinic_affiliation"]
        else:
            session['clinic'] = None

        if session['clinic'] in ['Tepati', 'KL', 'Knights Landing', 'Clinica Tepati']:
            session['clinic'] = "inventory"


        session['user'] = payload.get("role") #user will be either admin or viewer
        session['email'] = payload.get("email")

        if "full_name" in payload:
            session['fullname'] = payload["full_name"]
        elif "fullname" in payload:
            session['fullname'] = payload["fullname"]
        else:
            session['fullname'] = None

        session['first_name'] = payload.get("first_name")
        session['last_name'] = payload.get("last_name")

        session['role'] = payload.get("role")

        session['supervisor'] = False
        if session['role'] == 'supervisor':
            session['user'] = 'admin'
            session['supervisor'] = True

        return redirect(url_for("main_page"))

    except ExpiredSignatureError:
        return "Token expired", 401
    except InvalidTokenError as e:
        print("DEBUG: Invalid token error:", e)
        return "Invalid token", 401


# Path to JSON file storing users
USER_FILE = os.path.join(os.path.dirname(__file__), "users.json")
CLINIC_FILE = os.path.join(os.path.dirname(__file__), "clinics.json")

# Ensure the file exists
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump([], f, indent=4)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        first_name = request.form.get("first_name")
        fullname = request.form.get("fullname")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        role = request.form.get("role")
        clinic_code = request.form.get("clinic_affiliation").strip().upper()  # user-entered code

        # Load clinic code -> name map
        try:
            with open(CLINIC_FILE, "r") as f:
                clinics = json.load(f)
        except Exception as e:
            flash(f"Error loading clinics: {e}", "error")
            return redirect(url_for("login", view="register"))

        # Match code to clinic name
        clinic_name = clinics.get(clinic_code)
        if not clinic_name:
            flash("Invalid clinic code. Please try again.", "error")
            return redirect(url_for("login", view="register"))

        # Load or initialize user list
        try:
            with open(USER_FILE, "r") as f:
                users = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            users = []

        # Check if username already exists
        if any(u["email"] == email for u in users):
            flash("An account with that email already exists.", "error")
            return redirect(url_for("login", view="register"))
        
        # Auto-adjust viewer roles based on clinic code
        if role == "viewer":
            if clinic_code.upper() == "TEPATI":
                role = "tepati"
            elif clinic_code.upper() == "KLOHC":
                role = "klohc"

        # Create new user record
        new_user = {
            "username": username,
            "password": password,  # (plain text for now)
            "first_name": first_name,
            "fullname": fullname,
            "last_name": last_name,
            "email": email,
            "role": role,
            "clinic_code": clinic_code,           # store code
            "clinic_affiliation": clinic_name     # store name
        }

        # Save user
        users.append(new_user)
        with open(USER_FILE, "w") as f:
            json.dump(users, f, indent=4)

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for("login"))

    # GET request
    return render_template("signup.html")



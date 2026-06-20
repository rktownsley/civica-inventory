from app_context import *

@app.route('/sample')
def sample_page():
    return render_template('sample.html')


@app.route('/example_popup')
def example_popup():
    return render_template('example_popup.html')

@app.route('/search_bar_mockup')
def search_bar_mockup():
    return render_template('search_bar_mockup.html')

@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    print("debug 4529")
    name = request.form.get('name')
    email = request.form.get('email')
    type_ = request.form.get('type')
    topic = request.form.get('topic')
    message = request.form.get('message')
    rating = request.form.get('rating')

    file = request.files.get('file')
    saved_filename = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        saved_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(saved_filename)

    feedback_entry = {
        "timestamp": datetime.now(pytz.utc).astimezone(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S'),
        "name": name,
        "email": email,
        "type": type_,
        "topic": topic,
        "message": message,
        "rating": rating,
        "file": saved_filename
    }

    # Save to feedback.json
    if not os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

    with open(FEEDBACK_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data.append(feedback_entry)
        f.seek(0)
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Saved feedback:", feedback_entry)

    # ---- Send email ----
    try:
        msg = EmailMessage()
        msg['Subject'] = f"New Feedback Submission: {type_}"
        msg['From'] = SMTP_USERNAME
        msg['To'] = TO_EMAIL

        body = f"""
        You have received a new feedback submission.

        Name: {name}
        Email: {email}
        Type: {type_}
        Topic: {topic}
        Rating: {rating}
        Message:
        {message}
        """
        msg.set_content(body)

        # Attach file if exists
        if saved_filename:
            with open(saved_filename, "rb") as f:
                file_data = f.read()
                file_name = os.path.basename(saved_filename)
            msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        print("Email sent successfully.")
    except Exception as e:
        print("Error sending email:", e)

    # Flash success message and redirect
    flash("Thank you, your message has been sent.", "success")
    return redirect(url_for('login'))


@app.route('/view-feedback')
def view_feedback():
    if not os.path.exists(FEEDBACK_FILE):
        feedback_data = []
    else:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            feedback_data = json.load(f)

    # Fix file paths: convert absolute paths to /static/... URLs
    for entry in feedback_data:
        if entry.get("file"):
            # make it relative to static folder
            rel_path = os.path.relpath(entry["file"], app.root_path)
            entry["file_url"] = "/" + rel_path.replace("\\", "/")
        else:
            entry["file_url"] = None

    return render_template("view_feedback.html", feedback=feedback_data)



from app_context import app

# Import route modules so their @app.route decorators register endpoints.
import auth_routes  # noqa: F401
import inventory_routes  # noqa: F401
import settings_routes  # noqa: F401
import reports_routes  # noqa: F401
import misc_routes  # noqa: F401


if __name__ == '__main__':
    app.secret_key = 'your-secret-key'  # Replace with a secure random string in production

    # For running locally
    app.run(debug=True, host='0.0.0.0', port=5001)

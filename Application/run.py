from app import create_app
import os

# Create the Flask application
app = create_app(os.getenv('FLASK_CONFIG') or 'development')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)



from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from routes import routes_bp  # Import Blueprint from routes.py
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:your_password@localhost/offsideai'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static/uploads')

db = SQLAlchemy(app)

# Register Blueprint for routes
app.register_blueprint(routes_bp)

if __name__ == "__main__":
    app.run(debug=True)

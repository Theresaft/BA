# server/__init__.py
from flask import Flask
from flask_cors import CORS

from server.main.routes import main_blueprint
from server.auth.routes import auth_blueprint
from server.images.routes import images_blueprint
from server.database import db, create_cleanup_event
from server.models import *

def create_app():

    # instantiate the app
    app = Flask( __name__ )
    CORS(app, resources={r"/*": {"origins": "*"}}, expose_headers=["X-File-Type"], supports_credentials=True)  # Adjust origins as needed

    # Init database
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://user:user_password@mysqlDB:3306/my_database" 
    db.init_app(app)

    with app.app_context():
        db.create_all()
        create_cleanup_event()

    # register blueprints
    app.register_blueprint(main_blueprint, url_prefix='/brainns-api') # Alternativ zum brainns-api Prefix könnte man in Nginx den Prefix strippen
    app.register_blueprint(auth_blueprint, url_prefix='/brainns-api/auth')
    app.register_blueprint(images_blueprint, url_prefix='/brainns-api/images')

    # shell context for flask cli
    app.shell_context_processor({"app": app})

    return app

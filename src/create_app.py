import os

from flask import Flask

from views import blueprint


def create_app(testing=False):
    """Application factory, used to create application
    """
    app = Flask(__name__)
    app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/acme")
    if testing:
        app.config["TESTING"] = True
        app.config["MONGO_URI"] = os.environ.get(
            "MONGO_TEST_URI", "mongodb://localhost:27017/test_acme"
        )
    configure_extensions(app)
    register_blueprints(app)
    return app

def register_blueprints(app):
    """register all blueprints for application
    """
    app.register_blueprint(blueprint)

def configure_extensions(app):
    """configure flask extensions
    """
    from extensions import socketio, mongo
    mongo.init_app(app)
    socketio.init_app(app)
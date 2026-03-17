from flask import Flask
from config import config


def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Register blueprints
    from app.blueprints.rss import rss_bp
    app.register_blueprint(rss_bp)

    return app


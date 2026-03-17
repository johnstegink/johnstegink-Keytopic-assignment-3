from flask import Blueprint

rss_bp = Blueprint('rss', __name__)

from app.blueprints.rss import routes


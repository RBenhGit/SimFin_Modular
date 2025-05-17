# modules/routes/__init__.py
import os
from flask import Blueprint

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'templates'))

home_bp = Blueprint('home', __name__, template_folder=template_dir)
graphs_bp = Blueprint('graphs', __name__, template_folder=template_dir, url_prefix='/graphs')
valuations_bp = Blueprint('valuations', __name__, template_folder=template_dir, url_prefix='/valuations')

from . import home, graphs, valuations
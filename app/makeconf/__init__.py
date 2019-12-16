from flask import Blueprint

make_conf = Blueprint('make_conf', __name__)

from . import views

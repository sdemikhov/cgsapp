from flask import Blueprint

make_intf = Blueprint('make_intf', __name__)

from . import views

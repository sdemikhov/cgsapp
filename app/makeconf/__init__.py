from flask import Blueprint

from ..models import MandatoryVlan

make_conf = Blueprint('make_conf', __name__)

@make_conf.app_context_processor 
def inject_MandatoryVlan(): 
     return dict(MandatoryVlan=MandatoryVlan)

from . import views

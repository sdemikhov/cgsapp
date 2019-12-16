from flask import Blueprint
from ..models import Permission

main = Blueprint(
			'main', #blueprint name
			__name__ #blueprint location
			)

@main.app_context_processor 
def inject_permissions(): 
     return dict(Permission=Permission) 

from . import views, errors, forms

from flask import Blueprint

main = Blueprint(
			'main', #blueprint name
			__name__ #blueprint location
			)

from . import views, errors, forms

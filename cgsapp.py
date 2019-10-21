import os
from flask_migrate import Migrate

from app import create_app, db

#your really need these import to make migrate work
from app.models import User, Role


app = create_app(os.environ.get("FLASK_CONFIG") or 'default')
migrate = Migrate(app, db)

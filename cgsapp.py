import os
from flask_migrate import Migrate

from app import create_app, db

#your really need these import to make migrate work
from app.models import (User, Role, Registration, MKUInfo, SwitchModel,
                        StorageForMakeConfig, PCV, MandatoryVlan)


app = create_app(os.environ.get("FLASK_CONFIG") or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role, Registration=Registration,
                MKUInfo=MKUInfo, SwitchModel=SwitchModel,
                StorageForMakeConfig=StorageForMakeConfig, PCV=PCV,
                MandatoryVlan=MandatoryVlan)

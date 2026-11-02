from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from authlib.integrations.flask_client import OAuth
db=SQLAlchemy(); migrate=Migrate(); csrf=CSRFProtect(); oauth=OAuth()

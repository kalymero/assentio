from main import create_flask_app
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt

db = SQLAlchemy()
flask_bcrypt = Bcrypt()

args = {'db':db,
        'bcrypt':flask_bcrypt}

app = create_flask_app(**args)

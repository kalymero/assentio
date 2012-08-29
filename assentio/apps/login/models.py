from sqlalchemy import types

from flask import current_app
from flask.ext.login import UserMixin

from assentio import db
from assentio.utils import DBMixin


class Encrypted(types.TypeDecorator):

    impl = types.String

    def process_bind_param(self, value, dialect):
        # encrypt the password before storing in the db
        # if the encrypt extension is installed
        bcrypt = current_app.extensions.get('bcrypt', None)
        if bcrypt:
            return bcrypt.generate_password_hash(value)
        return value


class User(UserMixin, DBMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16), unique=True, nullable=False)
    password = db.Column(Encrypted(120), nullable=False)

    def __init__(self, username=None):
        self.username = unicode(username) or None

    def __repr__(self):
        return '<User %r>' % self.username

    # Required by admin interface
    def __unicode__(self):
        return self.username

    def check_password(self, plaintext_password):
        "Validate the password against the stored one"
        bcrypt = current_app.extensions.get('bcrypt', None)
        if bcrypt:
            try:
                return bcrypt.check_password_hash(self.password,
                                                    plaintext_password)
            # This happens in case of invalid salt
            except ValueError:
                return False
        else:
            # Bcrypt not installed, check plain text
            return self.password == plaintext_password

from datetime import datetime
from werkzeug.urls import url_fix

from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property

from flask.ext.login import current_user

from assentio import db
from assentio.utils import DBMixin

states = dict(private='Private', public='Public')
post_types = dict(standard='Standard', image='Image', quote='Quote',
                  page='Page', flashnews="Flash News")

page_categories = {'top-navigation': 'Top Navigation',
                   'bottom-navigation': "Bottom Navigation"}


class Post(DBMixin, db.Model):
    # '_'-prefixed column name are not shown by flask-admin
    id = db.Column(db.Integer, primary_key=True)
    stored_shortname = db.Column(db.String(120), unique=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    body = db.Column(db.Text, nullable=False)
    showfull = db.Column(db.Boolean)
    image = db.Column(db.String)
    date = db.Column(db.DateTime)
    type = db.Column(db.String(15), nullable=False, default='standard')
    state = db.Column(db.String(10), nullable=False, default='private')
    _author = db.Column(db.String(16))

    def __init__(self, title=None):
        if title:
            self.title = title

    def __repr__(self):
        return '<Post "%r">' % (self.title)

    # Required by admin interface
    def __unicode__(self):
        return self.title

    @validates('title')
    def validate_title(self, key, value):
        # When validating the title we also store the 'automatic' fields
        # It's weird but it seems to work as expected
        # We store the shortname if already exists or the title
        # the shortname validator, then, will normalize it
        self.stored_shortname = self.stored_shortname or value
        self._author = self._author or current_user.username
        self.date = self.date or datetime.now()
        return value

    @validates('stored_shortname')
    def validate_shortname(self, key, value):
        return url_fix(value.lower())

    @validates('state')
    def validate_state(self, key, value):
        assert value in states.keys()
        return value

    @validates('type')
    def validate_type(self, key, value):
        assert value in post_types.keys()
        return value

    @validates('date')
    def validate_date(self, key, value):
        "Prevent the null date override from the form"
        return value or self.date

    @hybrid_property
    def shortname(self):
        return self.stored_shortname

    @shortname.setter
    def shortname(self, value):
        self.stored_shortname = value

    @hybrid_property
    def author(self):
        return self._author

    @author.setter
    def author(self, value):
        self._author = value


class Page(DBMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(25), nullable=False,
                                            default='top-navigation')
    order = db.Column(db.Integer, nullable=False, default=1)
    post_id = db.Column(db.Integer, db.ForeignKey(Post.id))
    post = db.relationship('Post', backref=db.backref('page', lazy='dynamic'),
                           uselist=False,
                           primaryjoin="and_(Page.post_id==Post.id,"
                           "Post.type=='page')")

    def __repr__(self):
        if self.post:
            return '<Page "%r">' % (self.post.title)
        return '<Page with unbound post>'

    @validates('category')
    def validate_category(self, key, value):
        assert value in page_categories.keys()
        return value


class SocialButton(DBMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False)
    image = db.Column(db.String)
    url = db.Column(db.String)
    order = db.Column(db.Integer, nullable=False, default=1)
    disabled = db.Column(db.Boolean)
    state = db.Column(db.String(10), nullable=False, default='private')

    @validates('state')
    def validate_state(self, key, value):
        assert value in states.keys()
        return value

    def __repr__(self):
        return '<SocialButton "%r">' % (self.name)

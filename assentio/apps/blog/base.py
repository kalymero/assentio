import os

from sqlalchemy.orm import validates
from sqlalchemy.ext.declarative import declared_attr

from assentio import db
from assentio.utils import DBMixin, classproperty

from .slots import PortletSlot

template_folder = os.path.join(os.path.split(__file__)[0], 'templates')


class BasePortlet(DBMixin):
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(10), nullable=False, default='private')
    title = db.Column(db.String(120), nullable=False)
    order = db.Column(db.Integer, nullable=False, default=1)

    @declared_attr
    def slot_id(cls):
        return db.Column(db.Integer, db.ForeignKey(PortletSlot.id))

    @declared_attr
    def slot(cls):
        return db.relationship('PortletSlot',
                    backref=db.backref('portlet_%s' % (cls.__name__.lower()),
                                              lazy='dynamic'), uselist=False)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    @classproperty
    def type(cls):
        return cls.__name__.lower()

    @validates('state')
    def validate_state(self, key, value):
        from .models import states
        assert value in states.keys()
        return value

    def __init__(self):
        if self.type == 'baseportlet':
            raise RuntimeError

        super(BasePortlet, self).__init__()

    def __repr__(self):
        return '<%s "%s">' % (self.type, self.title)

    def get_template(self):
        "Must return the rendered template portlet"
        raise NotImplementedError

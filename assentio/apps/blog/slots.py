from assentio import db
from assentio.utils import DBMixin


class PortletSlot(DBMixin, db.Model):
    "Base class for slot management"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False, unique=True)
    description = db.Column(db.String(100))

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '<PortletSlot %s>' % self.name

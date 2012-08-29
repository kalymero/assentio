from assentio import db

from .base import BasePortlet


class TextPortlet(BasePortlet, db.Model):
    "The text portlet"
    body = db.Column(db.Text, nullable=False)

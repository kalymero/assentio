# -*- coding: utf-8 -*-

import os

from jinja2 import Template
from assentio import db

from .base import BasePortlet, template_folder


class TextPortlet(BasePortlet, db.Model):
    "The text portlet"
    body = db.Column(db.Text, nullable=False)

    def get_template(self):
        template_path = os.path.join(template_folder, 'portlets',
                                                          'textportlet.html')
        with open(template_path) as template:
            html = template.read()

        return Template(html).render(portlet=self)

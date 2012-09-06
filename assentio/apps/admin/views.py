from wtforms import fields as f, widgets as w

from wtforms.ext.sqlalchemy.orm import converts
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from flask.ext.admin import expose, AdminIndexView
from flask.ext.admin.form import ChosenSelectWidget
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.admin.contrib.sqlamodel.form import AdminModelConverter
from flask.ext.login import current_user, login_required
from assentio.apps.blog.models import (states, post_types, page_categories,
                                         Post)
from widgets import RichTextArea


class MyIndexView(AdminIndexView):
    @expose('/')
    @login_required
    def index(self):
        return self.render('admin/index.html')


# Adding coverter for the new Encrypted field
@converts('Encrypted')
def conv_Encrypted(self, field_args, **extra):
    field_args['widget'] = w.PasswordInput()
    self._string_common(field_args=field_args, **extra)
    return f.TextField(**field_args)

AdminModelConverter.conv_Encrypted = conv_Encrypted


class UnaccessibleModelView(ModelView):
    # Receive a 403 FORBIDDEN if not authenticated
    def is_accessible(self):
        return current_user.is_authenticated()


class PostModelView(UnaccessibleModelView):
    form_overrides = dict(state=f.SelectField, type=f.SelectField)
    form_args = dict(body=dict(widget=RichTextArea()),
                     state=dict(choices=states.items(), default='private'),
                     stored_shortname=dict(label='Shortname'),
                     type=dict(choices=post_types.items(),
                                                        default='standard'),)
    list_columns = ('id', 'shortname', 'type', 'title', 'date', 'author',
                                                                    'state')


class CustomQuerySelectField(QuerySelectField):
    widget = ChosenSelectWidget()

    def __init__(self, *args, **kwargs):
        kwargs['query_factory'] = lambda *whatever: \
                                    Post.query.filter(Post.type == 'page')
        super(CustomQuerySelectField, self).__init__(*args, **kwargs)


class PageModelView(UnaccessibleModelView):
    form_overrides = {'category': f.SelectField,
                      'post': CustomQuerySelectField}
    form_args = dict(category=dict(choices=page_categories.items(),
                        default='top-navigation'), order=dict(default=1))


class SocialButtonView(UnaccessibleModelView):
    form_overrides = dict(state=f.SelectField)
    form_args = dict(order=dict(default=1),
                     state=dict(choices=states.items(), default='private'),)


class PortletView(UnaccessibleModelView):
    form_overrides = dict(state=f.SelectField)
    form_args = dict(body=dict(widget=RichTextArea()),
                     order=dict(default=1),
                     state=dict(choices=states.items(), default='private'))
    list_columns = ('type', 'title', 'slot', 'order', 'state')

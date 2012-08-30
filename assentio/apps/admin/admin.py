import os
from flask.ext.admin import Admin

from flask import Blueprint, send_from_directory
from assentio import db
from assentio.apps.login.models import User
from assentio.apps.blog import Post, Page, SocialButton, TextPortlet
from assentio.apps.blog.slots import PortletSlot

from flask.ext.admin.contrib.fileadmin import FileAdmin

from views import (MyIndexView, UnaccessibleModelView, PostModelView,
                   PageModelView, SocialButtonView, PortletView)


class AdminApp(object):
    def __init__(self, app=None, app_name=None):
        # TODO: I should implement a singleton in the case
        # of the app is passed to the constructor
        # http://bit.ly/Pjc5N3, slide 64
        self.app = None
        if app and app_name:
            self.setup_app(app, app_name)

    def init_app(self, app, app_name):
        self.setup_app(app, app_name)

    def setup_app(self, app, app_name):
        assert self.app == None
        if not self.app:
            self.app = app

        self.__bp = Blueprint('admin_bp', __name__)

        admin = Admin(name=app_name,
                      index_view=MyIndexView(endpoint='adminview'))
        admin.init_app(self.app)

        # adding user view
        admin.add_view(UnaccessibleModelView(User, db.session))

        # adding blog post view
        admin.add_view(PostModelView(Post, db.session, category='Blog'))

        # adding PortletSlot
        admin.add_view(UnaccessibleModelView(PortletSlot, db.session,
                                                    category="Portlets"))

        # adding TextPortlet
        admin.add_view(PortletView(TextPortlet, db.session,
                                                    category="Portlets"))

        # adding pages view
        admin.add_view(PageModelView(Page, db.session, category="Contents"))

        # adding social_buttons view
        admin.add_view(SocialButtonView(SocialButton, db.session,
                                                    category="Contents"))

        # adding fileadmin view and creating the media path
        media_path = os.path.join(self.app.instance_path, 'media')
        if not os.path.exists(media_path):
            os.mkdir(media_path)
        admin.add_view(FileAdmin(media_path, '/media/', name='Files',
                                                    category='Blog'))

        # TIP: In a production environment media folder should be served by the
        # webserver itself or through a  CDN - as the static too
        @self.__bp.route('/media/<path:filename>')
        def media(filename):
            # Only for testing purpose
            if self.app.config.get('TESTING', None) and filename == 'anything':
                return 'OK'
            return send_from_directory(media_path, filename)

        self.app.register_blueprint(self.__bp)

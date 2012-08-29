import os

from flask import Blueprint, g
from flask.ext.login import LoginManager, current_user, login_user, logout_user

from .models import User
from .views import LoginView, LogoutView

template_folder = os.path.join(os.path.split(__file__)[0], 'templates')
login_bp = Blueprint('auth', __name__, template_folder=template_folder)


class ExtendedLoginManager(LoginManager):
    def init_app(self, app, add_context_processor=True):
        super(ExtendedLoginManager, self).init_app(app, add_context_processor)

        # define the load user method, applying the @user_loader decorator
        self.load_user = self.user_loader(self.load_user)

        # Login
        login_bp.add_url_rule('/login/',
                                view_func=LoginView.as_view('login_view'),
                                methods=['GET', 'POST'])

        # Helper required by Flask-login
        self.login_view = "auth.login_view"

        # Logout
        login_bp.add_url_rule('/logout',
                                view_func=LogoutView.as_view('logout_view'))

        app.register_blueprint(login_bp)

        if not hasattr(app, 'extensions'):
            app.extensions = {}

        # before_request handlers
        self.g_current_user = app.before_request(self.g_current_user)

        app.extensions['login_manager'] = self

    @staticmethod
    def load_user(userid):
        "Helper function required by Flask-login"

        user = User.query.filter_by(id=userid).first()
        return user or None

    @staticmethod
    def g_current_user():
        "Attach the current_user on the g object"
        g.user = current_user

    def validate_user(self, username, password):
        "Check for valid credentials"

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            return user
        return False

    def authenticate_user(self, username, password):
        "Authenticate user credendials"
        user = self.validate_user(username, password)
        if user:
            login_user(user)
            return True
        return False

    def logout_user(self):
        "Logout the current user"
        logout_user()

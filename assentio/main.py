import os
from flask import (Flask, render_template, Blueprint, current_app, request,
                   abort)
from flask_debugtoolbar import DebugToolbarExtension

from assentio.middlewares import SimpleCachingMiddleware

from utils import datetimeformat

MIDDLEWARES = (SimpleCachingMiddleware,)

# Applying the Application Factory pattern
# http://bit.ly/Pjc5N3, slide 53

bp = Blueprint('common', __name__)


# defining routes
@bp.route('/')
def index():
    blog_app = current_app.extensions['blog']

    # Retrieve the pagenumber for pagination if any
    # Default page is 1
    page = request.args.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        return abort(404)

    arguments = blog_app.get_all_page_components(page=page)
    return render_template('index.html', **arguments)


def create_flask_app(config_file=None, config_object=None, **kwargs):
    """Create and configure the Flask application. Accepted parameters are:
        :param db: A Flask-SQLAlchemy instance
        :param bcrypt: (optional) -> A Flask-Bcrypt instance
    """
    app = Flask(__name__)

    # Setting default values
    app.config['SECRET_KEY'] = 'test'
    app.debug = True

    # Creating instance path
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)

    if 'db' in kwargs:
        db_path = 'sqlite:///%s/%s' % (app.instance_path, 'blog.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = db_path

    # first override configurations from object if any
    if config_object:
        app.config.from_object(config_object)

    # then override configurations from file if any
    if config_file:
        app.config.from_pyfile(config_file)

    # then override configuration from envvar
    if 'ASSENTIO_SETTINGS' in os.environ:
        app.config.from_envvar('ASSENTIO_SETTINGS')

    if app.debug and not app.config.get('TESTING', None):
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
        app.config['DEBUG_TB_PROFILER_ENABLED'] = True
        app.config['DEBUG_TB_TEMPLATE_EDITOR_ENABLED'] = True
        DebugToolbarExtension(app)

    from .apps.login import LoginManager
    from .apps.admin import AdminApp
    from .apps.blog import BlogApp

    # Ensure we have an extensions registry on the app
    if not hasattr(app, 'extensions'):
        app.extensions = {}

    # registering apps / exensions
    if 'db' in kwargs:
        kwargs['db'].init_app(app)

    if 'bcrypt' in kwargs:
        kwargs['bcrypt'].init_app(app)
        # Store the bcrypt object in the extensions registry
        app.extensions['bcrypt'] = kwargs['bcrypt']

    login_manager = LoginManager()
    login_manager.init_app(app)
    AdminApp(app, 'assentio')
    BlogApp(app)

    # applying middlewares
    for mw in MIDDLEWARES:
        app.wsgi_app = mw(app.wsgi_app)

    app.register_blueprint(bp)

    # register jinja filters
    jinja_environment = app.create_jinja_environment()
    jinja_environment.filters['datetimeformat'] = datetimeformat
    app.create_jinja_environment = lambda *args: jinja_environment

    return app


def runserver():
    from . import app
    if app.config['TESTING'] == True:
        app.logger.error("Hey... you're running in TESTING mode.. keep your"
                         " eyes open")
    app.run()

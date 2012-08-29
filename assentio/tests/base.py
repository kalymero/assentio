import unittest

from flask.ext.login import AnonymousUser
from flask.ext.bcrypt import Bcrypt
from flask.ext.sqlalchemy import SQLAlchemy

from assentio import create_flask_app, db 
from assentio.manage import _syncdb as syncdb, _adduser as adduser
from assentio.apps.login import User
from assentio.apps.blog import Post

TESTUSER = 'testadmin'

class BaseTestCase(unittest.TestCase):

    def _get_an_app(self, with_bcrypt=False, with_new_db=False):
        if not with_new_db:
            db_to_use = db
        else:
            db_to_use = SQLAlchemy()

        args = {'db': db_to_use}

        if with_bcrypt:
            args ['bcrypt'] = Bcrypt()

        class TestingConfig(object):
            TESTING = True
            CSRF_ENABLED = False
            SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

        return create_flask_app(config_object=TestingConfig, **args)

    def setUp(self):

        self.app = self._get_an_app(with_bcrypt=True)
        ctx = self.app.app_context()
        ctx.push()
        
        self.client = self.app.test_client()

        # Disable password encryption: speeds up tests
        self.mock_bcrypt()
        
        # Creating DB
        syncdb(self.app)
        
        # Creating the test user
        adduser(TESTUSER, TESTUSER, self.app)
        
        # Useful location shortcuts
        self.login_location = '/login/'
        self.logout_location = '/logout'
        self.admin_location = '/admin/'
        self.media_location = '/media'


    def mock_bcrypt(self):
        'Disable password encryption'

        # Disabling password encryption improve the tests execution speed
        # I prefer monkeypatching the test because i don't want to expose any
        # 'disable_password_encryption' flag in the api

        bcrypt = self.app.extensions['bcrypt']
        bcrypt.generate_password_hash = lambda x: x
        bcrypt.check_password_hash = lambda x,y, *args: x==y

    def demock_bcrypt(self):
        'Enable password encryption'

        bcrypt = self.app.extensions['bcrypt']
        bcrypt.generate_password_hash = Bcrypt().generate_password_hash
        bcrypt.check_password_hash = Bcrypt().check_password_hash

    def login(self, username, pwd, follow_redirects=False):
        return self.client.post(self.login_location, data=dict(
        username=username,
        password=pwd), follow_redirects=follow_redirects)

    def logout(self):
        return self.client.get(self.logout_location, follow_redirects=True)

    def _fake_user_context(self, as_admin = False):
        """Injecting the TESTADMIN user in the fake request, if as_admin is False inject
        the AnonymousUser"""

        with self.app.test_request_context() as ctx:
           # We must be sure the before_request is raised
           self.app.preprocess_request()
           user = User.query.all()[0] if as_admin else AnonymousUser()
           ctx.user = user
           ctx.push()
           return ctx

    def create_post(self, title, body, shortname='', type=''):
        """Create a post"""
        # We must be logged-in to create a post
        ctx = self._fake_user_context(as_admin = True)

        tmp_post = Post(title)
        tmp_post.body = body
        if shortname:
            tmp_post.shortname = shortname

        if type:
            tmp_post.type = type

        # Reset the title in order to raise the title validator
        # which is responsible to set the shortname
        tmp_post.title = title
        tmp_post.save(self.app)
        
        # ok, throw away this crap
        ctx.pop()

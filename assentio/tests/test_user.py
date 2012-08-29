import unittest

from sqlalchemy.exc import IntegrityError
from assentio.tests import base
from assentio.apps.login import User


class UserComponentTestCase(base.BaseTestCase):

    def setUp(self):
        super(UserComponentTestCase, self).setUp()
        # Enabling password encryption only for this suite
        self.demock_bcrypt()

    def create_user(self, username, password, context_app=None):

        app = context_app or self.app
        user = User(username)
        user.password = password
        user.save(app)

    def test_create_user(self):
        "Test User creation and storage"
        
        pwd = 'test_password'

        # Create a User
        self.create_user('test_user_creation', pwd )

            
        # Check the post exists in the db
        user = User.query.filter_by(username='test_user_creation').first()
        self.assertTrue(user)
        
        # Test password is not stored in plain text
        self.assertNotEqual(user.password, pwd)

        # Test the password checking
        res = user.check_password(pwd)
        self.assertTrue(res)

    def test_no_user_duplicate(self):
        'Test cannot create duplicate user'

        self.create_user('duplicate', 'duplicate')
        with self.assertRaises(IntegrityError):
            self.create_user('duplicate', 'duplicate')

    def test_user_no_bcrypt(self):
        """Test the user creation in the case of no bcrypt is passed
            to the create_flask_app"""

        from assentio import db, create_flask_app
        from assentio.manage import _syncdb as syncdb  
       
        # Passing only the db param
        args = {'db':db}

        class TestingConfig(object):
            TESTING = True
            CSRF_ENABLED = False
            SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        
        # Creating a local app and create a user
        local_app = create_flask_app(config_object=TestingConfig, **args)
        syncdb(local_app)

        self.create_user('test_nobcrypt', 'test', local_app)

        with local_app.app_context():
            user = User.query.filter_by(username='test_nobcrypt').first()
            # Assert the user is created
            self.assertTrue(user)
            # Assert the password is stored as plaintext
            self.assertEqual(user.password, 'test')

    def test_user_on_g_object(self):
        "Checking the g object is correctly initialized for user auth"
       
        # Trying as anonymous
        ctx = self._fake_user_context()
        g = ctx.g
        self.assertFalse(g.user.is_authenticated())
        self.assertFalse(g.user.get_id())
        ctx.pop()

        # Ok, trying as admin
        ctx = self._fake_user_context(as_admin=True)
        g = ctx.g
        self.assertTrue(g.user.is_authenticated())
        self.assertEqual(g.user.get_id(), '1')
        ctx.pop()


def test_suite():
    tests_classes = [
        UserComponentTestCase,
    ]

    suite = unittest.TestSuite()

    suite.addTests([
        unittest.makeSuite(klass) for klass in tests_classes
    ])        

if __name__ == '__main__':
    unittest.main()

import os
import random
import unittest

from tempfile import NamedTemporaryFile, gettempdir

from assentio.tests import base
from assentio.main import create_flask_app
from assentio.manage import _syncdb as syncdb

class AssentioComponentTestCase(base.BaseTestCase):


    def test_cache_middeware(self):
        "Test the cache middleware is in place"
        res = self.client.get('/')
        self.assertIn("Cache-Control", res.headers)

    def test_sqlalchemy(self):
        "Test sqlalchemy is correctly instantiated"
        self.assertIn('sqlalchemy', self.app.extensions)

    def test_loginmanager(self):
        "Test login_manager is correctly instantiated"
        self.assertIn('login_manager', self.app.extensions)

    def test_blogapp(self):
        "Test the blog app is correctly instantiated"
        self.assertIn('blog', self.app.extensions)

    def test_media_folder(self):
        "Test the media folder is in place"
        res = self.client.get('%s/anything' % self.media_location)
        self.assertEqual(res.status_code, 200)

    def test_configurations(self):
        "Test handling configurations"

        # Creating an object configurion
        class TestConfig(object):
            CONFIG_TEST_VAR_OBJ = 'test'
        
        # Check the object configuration is working
        app = create_flask_app(config_object=TestConfig)
        self.assertIn('CONFIG_TEST_VAR_OBJ', app.config)

        # Creating a temp configuration file
        with NamedTemporaryFile(suffix='.py', delete=False) as tmp_config_file:
            tmp_config_file.write('CONFIG_TEST_VAR_FILE="test"')
            cfg_file_name = tmp_config_file.name

        # Check the configuration is in place
        app = create_flask_app(config_file=cfg_file_name)
        self.assertIn('CONFIG_TEST_VAR_FILE', app.config)

        # Check the configuration via environment variable
        os.environ['ASSENTIO_SETTINGS'] = cfg_file_name
        app = create_flask_app()
        self.assertIn('CONFIG_TEST_VAR_FILE', app.config)

        # Removing the property from the global environment
        os.environ.pop('ASSENTIO_SETTINGS')

        # We need to manually unlink the tmp file (delete=False)
        os.unlink(cfg_file_name)

    def test_syncdb_sqlite(self):
        "Test syncdb works properly wih sqlite"

        # creating a two level nested folder structure
        tmp = gettempdir()
        random_dir_1 = 'test_my_app-%s' % ''.join(map(str,random.sample(range(100),5)))
        random_dir_2 = 'test_my_app-%s' % ''.join(map(str,random.sample(range(100),5)))
        db_file_name = 'testapp.db'
        abs_path = os.path.join(tmp, random_dir_1, random_dir_2, db_file_name)

        # set the db path
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % abs_path

        # The path must not exists before the syncdb
        self.assertFalse(os.path.exists(abs_path))

        # launch the syncdb
        syncdb(self.app)

        # The path must exists after the syncdb
        self.assertTrue(os.path.exists(abs_path))

        # Trying with in-memory db
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        syncdb(self.app)
        

        
def test_suite():
    tests_classes = [
        AssentioComponentTestCase,
    ]

    suite = unittest.TestSuite()

    suite.addTests([
        unittest.makeSuite(klass) for klass in tests_classes
    ])        

if __name__ == '__main__':
    unittest.main()


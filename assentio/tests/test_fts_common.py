# -*- coding: utf-8 -*-
    
import unittest

from werkzeug.urls import url_fix
from assentio.tests import base
from assentio.tests.base import TESTUSER
from assentio.apps.blog import Post

STATUS_CODES = {'200': '200 OK',
                '301': '301 MOVED PERMANENTLY',
                '302': '302 FOUND',
                '400': '400 BAD REQUEST',
                '403': '403 FORBIDDEN',
                '404': '404 NOT FOUND'}


class AssentioFunctionalTestCase(base.BaseTestCase):

    def test_home_page(self):
        "Test home page is in place"
        res = self.client.get('/')
        self.assertIn('<!-- HomePage -->', res.data)

    def test_login_page(self):
        """Test the login process"""
        # Browse to the login page anche check redirect
        res = self.client.get('/login')
        self.assertEqual(res.status, STATUS_CODES['301'])

        login_location = res.headers['Location'].replace('http://localhost','')
        self.assertEqual(login_location, self.login_location)

        res = self.client.get(login_location)
        self.assertEqual(res.status, STATUS_CODES['200'])

        # Try a bad login name
        res = self.login('bad', TESTUSER)

        self.assertIn('Login Error', res.data)
        
        # Try a bad password
        res = self.login(TESTUSER,'bad')

        self.assertIn('Login Error', res.data)
        
        # Try correct credentials
        res = self.login(TESTUSER,TESTUSER, True)

        self.assertIn('Logged in', res.data)

        # ok so we are logged in, what if we return on the login page?
        res = self.client.get(login_location, follow_redirects=True)
        self.assertIn('Already logged in', res.data)

    def test_login_next(self):
        "Test the correct handling of the ?next login parameter"
        
        redirect_to = '/admin'

        # Go to the login page with redirect to the admin
        res = self.client.get('/login/?next=%s' % redirect_to)
    
        # Check the hidden next field is rendered
        self.assertIn('name="next" type="hidden" value="%s"' % redirect_to, res.data)
    
        # Login with the next parameter
        res = self.client.post(self.login_location, data=dict(
        username=TESTUSER,
        password=TESTUSER,
        next=redirect_to), follow_redirects=True)

        # Login and check if the redirect worked
        self.assertIn('Welcome to the ADMIN interface', res.data)

        # Try to redirect outbound 
        redirect_to = 'http://google.com'

        res = self.client.post(self.login_location, data=dict(
        username=TESTUSER,
        password=TESTUSER,
        next=redirect_to), follow_redirects=True)

        # and check we're redirected on home instead
        self.assertIn('<!-- HomePage -->', res.data)


    def test_admin_page(self):
        "Test the admin page"

        # Browse to the admin page anche check redirects
        res = self.client.get('/admin')
        self.assertEqual(res.status, STATUS_CODES['301'])

        admin_location = res.headers['Location'].replace('http://localhost','')
        self.assertEqual(admin_location, self.admin_location)

        # Ok we are anonymous so we must be redirected to the login
        res = self.client.get(admin_location)
        self.assertEqual(res.status, STATUS_CODES['302'])
        self.assertIn('login', res.headers['Location'])

        # Ok, now we log in
        self.login(TESTUSER, TESTUSER, True)

        # and return on the admin page
        res = self.client.get(admin_location)

        # and we are in!
        self.assertEqual(res.status, STATUS_CODES['200'])
        
        # and we are on the index page
        self.assertIn('Welcome to the ADMIN interface', res.data)

        # check we are not using local /admin resources
        self.assertNotIn('/admin/static', res.data)

    def test_admin_user_view(self):
        'Trying to create a user via admin interface'

        # Check the page in not accessible as anonymous
        res = self.client.get('/admin/userview/')
        self.assertEqual(res.status, STATUS_CODES['403'])

        # Login as superuser
        self.login(TESTUSER, TESTUSER)

        res = self.client.get('/admin/userview/')
        self.assertEqual(res.status, STATUS_CODES['200'])

        # Try to create a user

        res = self.client.post('/admin/userview/new/', data=dict(
        username='test',
        password='test'
        ) )
        
        self.assertNotIn('Failed to create model', res.data)

        # Try to log in as the new user
        self.logout()
        res = self.login('test','test', True)
        self.assertIn('Logged in', res.data)

    def test_admin_post_view(self):
        'Trying to create a post via admin interface'

        # Check the page in not accessible as anonymous
        res = self.client.get('/admin/postview/')
        self.assertEqual(res.status, STATUS_CODES['403'])

        # Login as superuser
        self.login(TESTUSER, TESTUSER)

        res = self.client.get('/admin/postview/')
        self.assertEqual(res.status, STATUS_CODES['200'])

        # Try to create a post
        
        post_title = u'test post with an à'
        res = self.client.post('/admin/postview/new/', data=dict(
        title=post_title,
        body='test_body',
        ) )
        
        self.assertNotIn('Failed to create model', res.data)
        
        # Check the post in the db
        post = Post.query.filter_by(title=post_title).first()
        self.assertTrue(post)

        # Chesk the post has a default date
        self.assertIsNotNone(post.date)

        # Check it has a normalized shortname
        self.assertEqual(post.shortname, url_fix(post.title.lower()))



    def test_logout(self):
        "The the logout process"

        res = self.logout()

        # ops we must be logged in..
        self.assertIn('Please log in to access', res.data)

        # so, login in first
        self.login(TESTUSER, TESTUSER, True)

        # Check the logout link is in place
        res = self.client.get(self.admin_location)
        self.assertIn('Logout', res.data)

        # and then logout
        res = self.logout()
        self.assertNotIn('_fresh', res.headers['Set-Cookie'])

    def test_pagination(self):
        "Check the pagination is working"

        self.login(TESTUSER,TESTUSER)

        # Let create 5 posts
        self.create_post('post-1', 'Post-1')
        self.create_post('post-2', 'Post-2')
        self.create_post('post-3', 'Post-3')
        self.create_post('post-4', 'Post-4')
        self.create_post('post-5', 'Post-5')

        # Go to the home, post-1 (older) must be not present
        res = self.client.get('/')
        self.assertNotIn('post-1', res.data)

        # But it must be present in page 2
        res = self.client.get('/?page=2')
        self.assertIn('post-1', res.data)

        # What happen if we redirect to a non existent page?
        res = self.client.get('/?page=3')
        # a 404 of course
        self.assertEqual(res.status, STATUS_CODES['404'])

        # and if the page number isn't a number? 
        res = self.client.get('/?page=not_a_number')
        # the same :D
        self.assertEqual(res.status, STATUS_CODES['404'])

    def test_caching(self):
        "Checking the Cache-Control header are correcly applyed"

        # As anonymous we have a sort of caching
        res = self.client.get('/')
        self.assertIn('max-age', res.headers['Cache-Control'])

        # Instead we manage no-cache for auth
        self.login(TESTUSER,TESTUSER)
        res = self.client.get('/')
        self.assertIn('no-cache', res.headers['Cache-Control'])

        # The Logout page must be NOT CACHED, or it will not work
        res = self.client.get(self.logout_location)
        self.assertIn('no-cache', res.headers['Cache-Control'])


        
def test_suite():
    tests_classes = [
        AssentioFunctionalTestCase,
    ]

    suite = unittest.TestSuite()

    suite.addTests([
        unittest.makeSuite(klass) for klass in tests_classes
    ])        

if __name__ == '__main__':
    unittest.main()


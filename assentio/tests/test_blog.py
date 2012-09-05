import unittest
from datetime import datetime, timedelta

from werkzeug.urls import url_fix
from sqlalchemy.exc import IntegrityError

from assentio.tests import base
from assentio.tests.base import TESTUSER
from assentio.manage import _syncdb as syncdb 
from assentio.apps.blog import Post, Page, SocialButton
from assentio.apps.blog.base import BasePortlet
from assentio.apps.blog.slots import PortletSlot

class BlogComponentTestCase(base.BaseTestCase):
    
    def test_create_post(self):
        "Test Post creation and storage"

        # Create a Post 
        self.create_post('My test Post', 'My Body')

        # Check the post exists in the db
        post = Post.query.filter_by(title='My test Post').first()

        self.assertTrue(post)
            
        # Check the post has a date
        self.assertTrue(post.date)

        # an author
        self.assertTrue(post.author)
        self.assertEqual(post.author, TESTUSER)

        # and a type (default = standard)
        self.assertTrue(post.type)
        self.assertEqual(post.type, 'standard')

        # Check it has a shortname and it's in lowercase
        self.assertTrue(post.shortname)
        self.assertEqual(post.shortname, url_fix(post.title.lower()))

        # and it's unique
        with self.assertRaises(IntegrityError): 
            self.create_post('My test Post', 'My Body')

        # Try to specify a custom shortname
        self.create_post('My test Post', 'Body', 'custom short name')

        # Check the post exists in the db
        post = Post.query.filter_by(shortname=url_fix('custom short name')).first()
        self.assertTrue(post)


    def test_post_visible(self):
        "Test the post is visibile after creation"

        self.create_post('My test Post', 'My Body')

        # Check the post exists in the db
        post = Post.query.filter_by(title='My test Post').first()

        # Check the default state is 'private'
        self.assertEqual(post.state, 'private')

        # and it's not accessible by anonymous
        res = self.client.get('/post/%s' % post.shortname)
        self.assertEqual(res.status_code, 404)

        # but it's accessible by authenticaded users
        self.login(TESTUSER, TESTUSER)
        res = self.client.get('/post/%s' % post.shortname)
        self.assertEqual(res.status_code, 200)

        # Ok, logout and...
        self.logout()

        # publish the post
        post.state = 'public'
        post.save(self.app)
        
        # Refresh the object
        post = Post.query.filter_by(title='My test Post').first()

        # Access the post by post id anche check the redirect
        res = self.client.get('/post/%d' % post.id)
        self.assertEqual(res.status_code, 302)
            
        # Access the post by shortname
        res = self.client.get('/post/%s' % post.shortname)
        self.assertEqual(res.status_code, 200)
        self.assertIn(post.title, res.data)

        # Access an unknown post
        res = self.client.get('/post/42')
        self.assertEqual(res.status_code, 404)
        res = self.client.get('/post/unknow')
        self.assertEqual(res.status_code, 404)
    

    def test_all_post_visibility(self):
        "Test the user visibily restrictions of the all posts method"
        
        # Injecting the anonymous user first
        ctx = self._fake_user_context()

        # Create three posts, one per kind [default state is private]
        self.create_post('post_1', 'post_body_1', type='standard')
        self.create_post('post_2', 'post_body_2', type='quote')
        self.create_post('post_3', 'post_body_3', type='image')

        # Ok we are anonymous so any of this posts is visible
        blog_app = self.app.extensions['blog']
        posts = blog_app.get_all_posts() 
        self.assertEqual(posts.count(), 0)
        
        # publish the first post
        post = Post.query.filter_by(title='post_1').first()
        post.state = 'public'
        post.save(self.app)

        # Now we must have one visible post
        posts = blog_app.get_all_posts() 
        self.assertEqual(posts.count(), 1)

        # or all the posts if we use the unresticted 
        posts = blog_app.get_all_posts(unrestricted=True) 
        self.assertEqual(posts.count(), 3)

        ctx.pop()

        # But forgot the unrestricted and let's authenticate
        ctx = self._fake_user_context(as_admin=True)
        
        # and we'll shown all the posts
        posts = blog_app.get_all_posts() 
        self.assertEqual(posts.count(), 3)

        # change the date and check for posts order
        
        post_1 = Post.query.filter_by(title='post_1').first()
        post_2 = Post.query.filter_by(title='post_2').first()

        post_1.date = datetime.now() 
        post_2.date = datetime.now() + timedelta(hours=1)

        self.assertTrue(post_2.date > post_1.date)

        post_1.save(self.app)
        post_2.save(self.app)

        posts = blog_app.get_all_posts(ordered=True) 

        self.assertEqual(posts[0].title, 'post_2')
        self.assertEqual(posts[1].title, 'post_1')

        # Now we create a page, it should not be visibile in all_posts
        # view so the posts must be 3
        self.create_post('post_4', 'post_body_4', type='page')

        posts = blog_app.get_all_posts() 
        self.assertEqual(posts.count(), 3)
        ctx.pop()

    def test_page(self):
        "Check page creation"
        
        # Create a standard post and page post
        self.create_post('page_post','page_post_body', type='page')
        self.create_post('standard_post','standard_post_body', type='standard')

        # And now create a page
        page = Page()

        page_post = Post.query.filter_by(title='page_post').first()

        # Relate the page_post with the page
        page.post = page_post
        page_post.save(self.app)
        page.save(self.app)

        page_post = Post.query.filter_by(title='page_post').first()
        page = Page.query.all()[0]

        self.assertIs(page.post, page_post)

        # Try to relate a standard post to a page (it's not allowed)
        standard_post = Post.query.filter_by(title='standard_post').first()
        page.post = standard_post 
        standard_post.save(self.app)
        page.save(self.app)

        page = Page.query.all()[0]

        self.assertIsNone(page.post)

    def test_page_order(self):
        "Checking the page order is respected"

        # Create two page post
        self.create_post('page_post_1','page_post_body', type='page')
        self.create_post('page_post_2','page_post_body', type='page')

        ctx = self._fake_user_context(as_admin = True)

        # and two pages
        page_1 = Page()
        page_2 = Page()

        # Applying an order and saving
        page_post_1 = Post.query.filter_by(title='page_post_1').first()
        page_1.post = page_post_1
        page_1.order = 2
        page_post_1.save(self.app)
        page_1.save(self.app)

        page_post_2 = Post.query.filter_by(title='page_post_2').first()
        page_2.post = page_post_2
        page_2.order = 1
        page_post_2.save(self.app)
        page_2.save(self.app)

        # Checking the order is respected
        blog_app = self.app.extensions['blog']
        pages = blog_app.get_pages(ordered=True)

        self.assertEqual(pages[0].post.title, 'page_post_2')
        self.assertEqual(pages[1].post.title, 'page_post_1')
        ctx.pop()

    def test_social_buttons(self):
        "Checking social buttons"

        # Login as anonymous
        ctx = self._fake_user_context()

        # Creating two buttons, the order specify twitter before fb
        sb1 = SocialButton()
        sb1.name = 'Facebook'
        sb1.order = 2
        sb1.save(self.app)

        sb2 = SocialButton()
        sb2.name = 'Twitter'
        sb2.order = 1
        sb2.save(self.app)

        blog_app = self.app.extensions['blog']

        # check they're safely stored and retrieved 
        # Default is private so it must be 0
        btns = blog_app.get_social_buttons()
        self.assertEqual(btns.count(), 0)

        # ok, let me login in as autenticated
        ctx.pop()
        ctx = self._fake_user_context(as_admin=True)

        # Retieve it in ordered sequence
        btns = blog_app.get_social_buttons(ordered=True)
        self.assertEqual(btns[0].name,'Twitter')
        self.assertEqual(btns[1].name,'Facebook')

        ctx.pop()

    def test_portlet(self):
        "Check portlets engine"
        
        db = self.app.extensions['sqlalchemy'].db 
        blog_app = self.app.extensions['blog']

        # defining a TestPortlet Type
        class TestPortlet(BasePortlet, db.Model):
            pass

        # Updating the portlets
        blog_app.update_portlets(TestPortlet)

        # Resync the db so the new table is created
        syncdb(self.app)

        # Tryng to instantiate a BasePortlet, it's not possible
        with self.assertRaises(RuntimeError):
            BasePortlet()

        # Let's try again
        test_portlet = TestPortlet() 
        test_portlet.title = 'Test Portlet'
        test_portlet.save(self.app)

        # Let's create a new TestPortlet instance
        test_portlet_2 = TestPortlet()
        test_portlet_2.title = 'Test Portlet 2'

        # check the type 
        self.assertEqual(test_portlet_2.type, 'testportlet')

        # and the string representation
        self.assertEqual(test_portlet_2.__repr__(), '<testportlet "Test Portlet 2">')

        # check the type is in the extension registry
        self.assertIn(test_portlet_2.type, self.app.extensions['blog_portlets'])

        # check get_template raise a NotImplementedError
        with self.assertRaises(NotImplementedError):
            test_portlet_2.get_template()

    def test_slots(self):
        "Check slots working"
        
        # Login as anonymous
        ctx = self._fake_user_context()

        db = self.app.extensions['sqlalchemy'].db 
        blog_app = self.app.extensions['blog']

        # Create a new kind of porlet
        class MyPortlet(BasePortlet, db.Model):
            pass

        # Updating the portlets
        blog_app.update_portlets(MyPortlet)

        syncdb(self.app)

        # Create a Slot an portlet related with it
        test_slot = PortletSlot()
        test_slot.name = "slot"

        portlet = MyPortlet()
        portlet.title = 'My Portlet'
        portlet.slot = test_slot
        portlet.order = 2

        portlet2 = MyPortlet()
        portlet2.title = 'My Portlet 2'
        portlet2.slot = test_slot
        portlet2.order = 1 

        db.session.add(test_slot)
        db.session.add(portlet)
        db.session.add(portlet2)
        db.session.commit()

        portlets = blog_app.get_portlets_by_slot('another_slot')
        
        # There are no porlets on that slot
        self.assertEqual(len(portlets), 0)

        # so, check for our slot
        portlets = blog_app.get_portlets_by_slot('slot')
        
        # Now there're 2 portlets, but we are anoymous so we expect 0
        self.assertEqual(len(portlets), 0)

        # so let's authenticate
        ctx.pop()
        ctx = self._fake_user_context(as_admin=True)
        
        portlets = blog_app.get_portlets_by_slot('slot', ordered=True)

        # and now there are 2
        self.assertEqual(len(portlets), 2)

        # Check they're ordered
        self.assertEqual(portlets[0].title, 'My Portlet 2')
        self.assertEqual(portlets[1].title, 'My Portlet')

        ctx.pop()
        
def test_suite():
    tests_classes = [
        BlogComponentTestCase,
    ]

    suite = unittest.TestSuite()

    suite.addTests([
        unittest.makeSuite(klass) for klass in tests_classes
    ])        

if __name__ == '__main__':
    unittest.main()

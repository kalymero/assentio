import os

from flask import Blueprint, render_template, url_for, redirect, current_app
from flask.ext.login import current_user

from .models import Post, Page, SocialButton, post_types
from .slots import PortletSlot
from .portlets import TextPortlet

template_folder = os.path.join(os.path.split(__file__)[0], 'templates')
blog_bp = Blueprint('blog', __name__, template_folder=template_folder)


@blog_bp.route("/post/<int:post_id>")
@blog_bp.route("/post/<shortname>")
def post(post_id=None, shortname=None):
    blog_app = current_app.extensions['blog']

    search_index = 'shortname' if shortname else 'id'
    search_value = shortname or post_id

    search_args = {search_index: search_value}

    # If anonymous user search only for published posts
    if not current_user.is_authenticated():
        search_args['state'] = 'public'

    post = Post.query.filter_by(**search_args).first_or_404()

    if search_index == 'id':
        return redirect(url_for('.post', shortname=post.shortname))
    else:
        arguments = blog_app.get_all_page_components(post=post)
        return render_template("post.html", **arguments)


class BlogApp(object):

    def __init__(self, app=None):
        self.app = app
        self._init_app()

    def init_app(self, app):
        assert self.app == None
        self.app = app
        self._init_app()

    def _init_app(self):
        # make sure we have the extensions registry
        if not hasattr(self.app, 'extensions'):
            self.app.extensions = {}

        # Storing the app into the extension registry
        self.app.extensions['blog'] = self

        # Prepare the registry to store portlets and store the basics one
        self.app.extensions['blog_portlets'] = set()
        self.update_portlets(TextPortlet)

        self.app.register_blueprint(blog_bp)

    def update_portlets(self, portletclass):
        """Update the registered portlet types
          :param portletclass: is the portlet class you want to register
        """
        self.app.extensions['blog_portlets'].add(portletclass.type)

    def _get_posts(self, types=[], unrestricted=False, ordered=False):
        """Wrapped method which simply return posts
        :param types: if [] return all types post else returns only the
                      specified ones
        :param unrestricted: if True bypass the security check"""

        search_args = {}

        # Filter for the specified types
        posts = Post.query.filter(Post.type.in_(types))

        # If anonymous user search only for published posts
        if not current_user.is_authenticated() and not unrestricted:
            search_args['state'] = 'public'

        # Apply more filters if any
        if search_args:
            posts = posts.filter_by(**search_args)

        if ordered:
            posts = posts.order_by(Post.date.desc())

        return posts

    def get_all_posts(self, unrestricted=False, ordered=False):
        "Return all the post visibile by the user"
        # Remove only the static type from all the available types
        filter_types = post_types.keys()
        filter_types.remove('page')
        return self._get_posts(types=filter_types, unrestricted=unrestricted,
                                                        ordered=ordered)

    def get_pages(self, unrestricted=False, ordered=False):
        "Return the pages"

        pages = Page.query

        # If anonymous user search only for published posts
        if not current_user.is_authenticated() and not unrestricted:
            pages = pages.join(Post).filter(Post.state == 'public')

        if ordered:
            pages = pages.order_by(Page.order)

        # Return only pages with an attached post
        return filter(lambda p: p.post, pages)

    def get_social_buttons(self, unrestricted=False, ordered=False):
        "Return the social buttons"

        search_args = {}
        btns = SocialButton.query

        # If anonymous user search only for published posts
        if not current_user.is_authenticated() and not unrestricted:
            search_args['state'] = 'public'

        btns = btns.filter_by(**search_args)

        if ordered:
            btns = btns.order_by(SocialButton.order)

        return btns

    def get_portlets_by_slot(self, name, unrestricted=False, ordered=False):
        "Return all the portlets related to a slot"
        portlets = []
        slot = PortletSlot.query.filter(PortletSlot.name == name)

        # The slot does not exist
        if not slot.count():
            return portlets

        slot = slot[0]

        portlet_types = self.app.extensions['blog_portlets']

        for ptype in portlet_types:
            portlets.extend(getattr(slot, 'portlet_%s' % ptype))

        # If anonymous user search only for published posts
        if not current_user.is_authenticated() and not unrestricted:
            portlets = filter(lambda x: x.state == 'public', portlets)

        if ordered:
            portlets.sort(key=lambda portlet: portlet.order)

        return portlets

    def get_all_page_components(self, post=None, page=None):
        "Return all elements needed to correctly render the page"

        arguments = {}

        if post:
            arguments['post'] = post
        else:
            if page:
                arguments['posts'] =\
                            self.get_all_posts(ordered=True).paginate(page, 4)
            else:
                arguments['posts'] = self.get_all_posts(ordered=True)

        arguments['pages'] = self.get_pages(ordered=True)
        arguments['social_buttons'] = self.get_social_buttons(ordered=True)

        # add the function so it can be retrieved from the template
        arguments['get_portlet_by_slot'] = self.get_portlets_by_slot

        return arguments

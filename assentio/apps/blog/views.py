import datetime

from urlparse import urljoin
from PyRSS2Gen import RSS2, RSSItem, Guid

from flask import (redirect, url_for, current_app, render_template,
                    make_response, request)
from flask.ext.login import current_user

from .blog import blog_bp
from .models import Post


@blog_bp.route('/post/<int:post_id>')
@blog_bp.route('/post/<shortname>')
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


@blog_bp.route('/feed')
def rss():
    blog_app = current_app.extensions['blog']
    posts = blog_app.get_all_posts(ordered=True)
    host = request.url_root
    items = []

    for post in posts:
        post_url = urljoin(host, url_for('blog.post', post_id=post.id))
        rss = RSSItem(title=post.title,
                      link=post_url,
                      description=post.description,
                      guid=Guid(post_url),
                      pubDate=post.date)
        items.append(rss)

    feed = RSS2(title='Progress in Development',
                link=url_for('blog.rss'),
                description='Antonio Sagliocco personal blog',
                lastBuildDate=datetime.datetime.now(),
                items=items)

    response = make_response(feed.to_xml())
    response.mimetype = 'application/rss+xml'
    return response

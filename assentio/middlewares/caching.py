from time import mktime

from wsgiref.handlers import format_date_time
from datetime import datetime, timedelta

from flask import url_for, request
from flask.ext.login import current_user


class SimpleCachingMiddleware(object):
    "Apply the cache-control header"

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Apply a simple cache-control header. 30 seconds for auth users, no
        # caching for anon

        # HTTP/1.1
        no_cache = [('Cache-Control', 'no-cache private')]

        # HTTP/1.0 - Datetime in RFC 1123 format
        expires_on = datetime.now() + timedelta(seconds=30)
        expires_on = mktime(expires_on.timetuple())
        expires_on = format_date_time(expires_on)

        minimal_caching = [('Cache-Control', 'public, max-age=30'),
                           ('Expires', expires_on)]

        def _start_response(status, response_headers, exc_info=None):
            # Logout view must be not cached or it will not work
            not_caching_urls = (url_for('auth.logout_view'),
                                url_for('blog.rss'))

            if not current_user.is_authenticated() and request.path not in \
                                                            not_caching_urls:
                response_headers.extend(minimal_caching)
            else:
                response_headers.extend(no_cache)

            return start_response(status, response_headers, exc_info)
        return self.app(environ, _start_response)

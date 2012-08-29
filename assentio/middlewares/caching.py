from flask import url_for, request
from flask.ext.login import current_user


class SimpleCachingMiddleware(object):
    "Apply the cache-control header"

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Apply a simple cache-control header. 5 Minutes for auth users, no
        # caching for anon

        no_cache = [('Cache-Control', 'no-cache private')]
        five_min_cache = [('Cache-Control', 'public, max-age=30')]

        def _start_response(status, response_headers, exc_info=None):
            # Logout view must be not cached or it will not work
            not_caching_urls = (url_for('auth.logout_view'), )

            if not current_user.is_authenticated() and request.path not in \
                                                            not_caching_urls:
                response_headers.extend(five_min_cache)
            else:
                response_headers.extend(no_cache)

            return start_response(status, response_headers, exc_info)
        return self.app(environ, _start_response)

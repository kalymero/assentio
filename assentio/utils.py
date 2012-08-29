

# Mixin class for db.Model with some convenience methods
class DBMixin(object):

    def save(self, app):
        "Convenience method to save a model"
        with app.app_context():
            app.extensions['sqlalchemy'].db.session.add(self)
            app.extensions['sqlalchemy'].db.session.commit()


# DateTime conversion template filter
def datetimeformat(value, format="%d %B %Y"):
    "Format the datetime (default is in the format: '23 August 2012')"
    return value.strftime(format)


# @classproperty decorator
class classproperty(object):
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)

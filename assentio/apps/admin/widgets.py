from cgi import escape
from wtforms.widgets import TextArea
from wtforms.widgets.core import HTMLString, html_params


class RichTextArea(TextArea):
    """
    Renders a multi-line text area.

    `rows` and `cols` ought to be passed as keyword args when rendering.
    """
    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        return HTMLString(u'<textarea class="ckeditor" %s>%s</textarea>' %
                         (html_params(name=field.name, **kwargs),
                          escape(unicode(field._value()))))

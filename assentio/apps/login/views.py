from urlparse import urlparse, urljoin

from flask import (request, render_template, abort, redirect, current_app,
                   views, url_for, flash, escape)

from flask.ext.wtf import Form, TextField, HiddenField, Required
from flask.ext.login import current_user, login_required


class LoginForm(Form):
    username = TextField('username', validators=[Required()])
    password = TextField('password', validators=[Required()])
    # hiddend next filed required for redirection
    next = HiddenField('next')

    def is_safe_url(self, target):
        ref_url = urlparse(request.host_url)
        test_url = urlparse(urljoin(request.host_url, target))
        return test_url.scheme in ('http', 'https') and \
               ref_url.netloc == test_url.netloc


class LoginView(views.MethodView):
    def __init__(self, *args, **kwargs):
        super(LoginView, self).__init__(*args, **kwargs)
        self._form = LoginForm(next=request.args.get('next', None))
        self._lm = current_app.extensions['login_manager']
        self.arguments = current_app.extensions['blog'].get_all_page_components()

    def get(self):
        if not current_user.is_anonymous():
            flash('Already logged in')
            return redirect(url_for('common.index'))
        return render_template("login.html", form=self._form, **self.arguments)

    def post(self):
        if self._form.validate_on_submit():
            username = self._form.data.get('username', None)
            password = self._form.data.get('password', None)

            if self._lm.authenticate_user(username, password):
                flash("Logged in successfully.")
                next_param = request.form.get("next", None)

                # Escaping if != None for security reason
                next_param = next_param and escape(next_param)

                # Only local redirect allowed
                if not self._form.is_safe_url(next_param):
                    next_param = None

                return redirect(next_param or url_for("common.index"))
            else:
                flash("Login Error")
                return render_template("login.html", form=self._form,
                                                    **self.arguments)

        # CSRF Violation
        abort(400)


class LogoutView(views.View):
    def __init__(self, *args, **kwargs):
        super(LogoutView, self).__init__(*args, **kwargs)
        self._lm = current_app.extensions['login_manager']

    @login_required
    def dispatch_request(self):
        self._lm.logout_user()
        return redirect(url_for('common.index'))

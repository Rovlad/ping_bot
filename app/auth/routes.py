from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app.auth import auth_bp
from app.auth.forms import LoginForm, SignupForm
from app.extensions import db
from app.models import User


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash('Logged in successfully.', 'success')
            return redirect(next_page or url_for('dashboard.index'))
        flash('Invalid email or password.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = SignupForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower(),
            password_hash=generate_password_hash(form.password.data),
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Account created! Please link your Telegram bot.', 'success')
        return redirect(url_for('settings.index'))

    return render_template('auth/signup.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required
from datetime import datetime

from . import auth
from .forms import LoginForm, RegistrationForm
from ..models import User, Registration
from app import db


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            _next = request.args.get('next')
            #may be need more safety url check
            if not _next or not _next.startswith('/'):
                _next = url_for('main.index')
            return redirect(_next)
        flash('Неправильный логин или пароль')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из учетной записи')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    registration = Registration.query.get(1)
    if registration.expired < datetime.now():
        flash('В данный момент регистрация закрыта, обратитесь к'
              ' администратору')
        redirect(url_for('auth.register'))
    if form.validate_on_submit():
        user = User(first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    email=form.email.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Пользователь успешно зарегистрирован, теперь вы можете войти')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

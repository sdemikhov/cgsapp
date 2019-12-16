from flask import render_template, flash, redirect, url_for
from flask_login import login_required

from datetime import datetime

from app import db
from ..models import User, Role, Registration
from .forms import ManageUsersForm
from ..decorators import admin_required
from . import main


@main.route('/')
def index():
	return render_template('index.html')


@main.route('/secret')
@login_required
def secret():
    return render_template('secret.html')


@main.route('/manage_users', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_users(): 
    users = {user.id: user for user in User.query.all()}
    roles = {role.id: role for role in Role.query.all()}
    registration = Registration.query.first()
    form = ManageUsersForm(
        sorted([(user_id, f'{user.first_name} {user.last_name}: "{user.role.name}"')
         for user_id, user in users.items()], key=lambda x: x[0]),
        [(role_id, f'Назначить роль {role.name}') 
        for role_id, role in roles.items()]
        )
    if form.validate_on_submit():
        if form.registration.data:
            registration.expired = form.registration.data
            flash(f'Регистрация открыта до {registration.expired}')
            db.session.add(registration)
        if form.users.data and form.edit.data != 0:
            for user_id in form.users.data:
                user = users[user_id]
                user.role = roles[form.edit.data]
                flash(f'Изменена учетная запись '
                      f'"{user.first_name} {user.last_name}"')
                db.session.add(user)
        db.session.commit()
        return redirect(url_for('main.manage_users'))
        
    form.registration.data = registration.expired
    return render_template('manage_users.html', form=form,
                           expired=registration.expired)

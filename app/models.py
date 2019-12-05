from flask_login import UserMixin, AnonymousUserMixin
from . import db, login_manager
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class Permission:
    NOT_APPROVED = 1
    CPE_n_preconf_SW = 16
    P2P = 32
    SW_n_AP = 64
    BRAS = 128
    ADMIN = 256


class Registration(db.Model):
    __tablename__ = 'registration'
    id = db.Column(db.Integer, primary_key=True)
    expired = db.Column(db.DateTime)

    @staticmethod
    def insert_expired(datetime_str):
        expired = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        db.session.add(Registration(expired=expired))
        db.session.commit()

    def __repr__(self):
        return f'registration expire {self.registration_expire}'


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'Not_approved': [Permission.NOT_APPROVED],
            'Network_engineer': [Permission.NOT_APPROVED,
                                 Permission.CPE_n_preconf_SW, 
                                 Permission.P2P,
                                 Permission.SW_n_AP,
                                 Permission.BRAS],
            'Administrator': [Permission.NOT_APPROVED,
                              Permission.CPE_n_preconf_SW, 
                              Permission.P2P,
                              Permission.SW_n_AP,
                              Permission.BRAS,
                              Permission.ADMIN],
        }
        default_role = 'Not_approved'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['CGSAPP_ADMIN']:
                self.role = Role.query.filter_by(
                                        name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first() 

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def __repr__(self):
        return f'<User {self.first_name} {self.last_name}>'


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

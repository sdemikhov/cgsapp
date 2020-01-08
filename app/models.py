from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import yaml
from collections import namedtuple
import ipaddress
from itertools import count

from . import db, login_manager
from .common_functions import convert_to_list


class Permission:
    NOT_APPROVED = 1
    CPE_n_preconf_SW = 16
    P2P = 32
    SW_n_AP = 64
    BRAS = 128
    ADMIN = 256


class MandatoryVlan:
    ur_pppoe = 200
    multicast = 4024

    @classmethod
    def get_all(self):
        return [self.ur_pppoe, self.multicast]


class PCV:
    @staticmethod
    def generate_groups():
        c = count()
        groups = [
            (next(c), f'{2200 + hundred + dozen}-{2200 + hundred + dozen+29}')
             for hundred in range(0, 701, 100)
             for dozen in range(1, 62, 30)
        ]
        return groups

    @classmethod
    def get_pcv_group(self, idx):
        _, group = self.generate_groups()[idx]
        start_vlan, end_vlan = group.split('-')
        return [vlan for vlan in range(int(start_vlan),
                                       int(end_vlan)+1)]

    @classmethod
    def get_pcv_group_with_related(self, idx):
        result = []
        for i in range(idx + 1):
            result += self.get_pcv_group(i)
        return result


class SwitchModel(db.Model):
    __tablename__ = 'switch_model'
    id = db.Column(db.Integer, primary_key=True)
    manufacturer = db.Column(db.String(64), nullable=False)
    model = db.Column(db.String(64), nullable=False)
    port_names = db.Column(db.String(256), nullable=False)

    @staticmethod
    def insert_switch_model():
        Switch_Model = namedtuple('Switch_Model',
                                  'manufacturer model port_names')
        with open('switch_model_info.yaml') as f:
            all_switch_model_info = yaml.load(f)
        for s in all_switch_model_info:
            s = Switch_Model(*s)
            switch = SwitchModel.query.filter_by(model=s.model).first()
            if switch is None:
                switch = SwitchModel(manufacturer = s.manufacturer,
                                     model = s.model,
                                     port_names = s.port_names)
                db.session.add(switch)
        db.session.commit()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ports = self.port_names.split(',')

    def __repr__(self):
        return f'<SwitchModel {self.manufacturer}_{self.model}>'


class StorageForMakeConfig(db.Model):
    __tablename__ = 'storage_for_make_config'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        unique=True, nullable=False)
    mku_info_id = db.Column(db.Integer, db.ForeignKey('mku_info.id'))
    step = db.Column(db.String(64))
    switch_model_id = db.Column(db.Integer,
                                db.ForeignKey('switch_model.id'))
    hostname = db.Column(db.String(64))
    ipaddress = db.Column(db.String(64))
    gateway = db.Column(db.String(64))
    netmask = db.Column(db.String(64))
    mng_vlan = db.Column(db.Integer)
    client_ports = db.Column(db.String(64))
    vlan_character = db.Column(db.String(64))
    PCV_group = db.Column(db.Integer)
    pppoe_single_vlan = db.Column(db.Integer)
    switches_ports = db.Column(db.String(64))
    switches_ports_vlans = db.Column(db.String(64))
    switches_ports_uplink = db.Column(db.String(64))

    @property
    def pcv_by_client_ports(self):
        ports = [int(i) - 1 for i in convert_to_list(self.client_ports)]
        if self.PCV_group or self.PCV_group == 0:
            vlans = PCV.get_pcv_group(self.PCV_group)
            return [vlans[i] for i in ports]
        return []

    def as_dict(self):
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_') and 'id' not in key:
                result[key] = value
        return result


class MKUInfo(db.Model):
    __tablename__ = 'mku_info'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    network = db.Column(db.String(64), unique=True, nullable=False)
    gateway = db.Column(db.String(64), unique=True, nullable=False)
    mng_vlan = db.Column(db.Integer)

    @staticmethod
    def insert_mku_info():
        MKU = namedtuple('MKU', 'name network gateway mng_vlan')
        with open('mku_info.yaml') as f:
            all_mku_info = yaml.load(f)
        for m in all_mku_info:
            m = MKU(*m)
            mku = MKUInfo.query.filter_by(name=m.name).first()
            if mku is None:
                mku = MKUInfo(name = m.name,
                              network = m.network,
                              gateway = m.gateway,
                              mng_vlan = m.mng_vlan)
                db.session.add(mku)
        db.session.commit()

    @property
    def netmask(self):
        network = ipaddress.IPv4Network(self.network)
        return str(network.netmask)

    def __repr__(self):
        return f'<MKUInfo {self.name}>'


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
        return f'<registration expire {self.registration_expire}>'


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

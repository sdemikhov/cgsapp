from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, SelectField, RadioField, SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired, IPAddress, Required
import ipaddress

from ..common_functions import convert_to_list
from ..models import StorageForMakeConfig, SwitchModel


class CheckHostname:
    def __init__(self, message=None):
        self._forbidden_hostname_symbols = ['#', '>', '%', '!']

    def __call__(self, form, field):
        if not field.data:
            raise ValidationError('Необходимо заполнить Hostname')
        for symbol in self._forbidden_hostname_symbols:
            if symbol in field.data:
                msg = (
                f'запрещены символы '
                f'{", ".join(self._forbidden_hostname_symbols)}'
                )
                raise ValidationError(msg)


class CheckNetmask:
    def __init__(self, message=None):
        if not message:
            message = u'Неверный формат маски подсети'
        self.message = message

    def __call__(self, form, field):
        try:
            ip = ipaddress.IPv4Interface(f'192.168.0.1/{field.data}') 
        except ipaddress.NetmaskValueError:
            raise ValidationError(self.message)


class CheckIPConnectivity:
    def __init__(self, message=None):
        if not message:
            message = ('Введенные ip-адрес и шлюз по умолчанию'
                       ' не принадлежат одной подсети')
        self.message = message

    def __call__(self, form, field):
        try:
            ip = ipaddress.IPv4Interface(
                f'{form.ipaddress.data}/{form.netmask.data}'
                ) 
            gw = ipaddress.IPv4Interface(
                f'{form.gateway.data}/{form.netmask.data}'
                )
            if not ip.network == gw.network:
                raise ValueError
        except (ipaddress.NetmaskValueError,
                ipaddress.AddressValueError, ValueError):
            raise ValidationError(self.message)


class CheckPorts:
    def __init__(self, message=None):
        if not message:
            message = ('Неверный формат')
        self.message = message

    def __call__(self, form, field):
        try:
            ports = convert_to_list(field.data)
            if not ports:
                raise ValueError
            for port in ports:
                int(port)
        except (ValueError, AttributeError):
            raise ValidationError(self.message)


class CheckPortsRange:
    def __init__(self, message=None):
        if not message:
            message = ('Порт {port} не укладывается в диапазон от 1'
                       ' до максимального порта {maximum} у'
                       ' модели {model}')
        self.message = message

    def __call__(self, form, field):
        storage = StorageForMakeConfig.query.filter_by(
            user_id=current_user.id
            ).first()
        sw_model = SwitchModel.query.get(storage.switch_model_id)
        ports = [int(port) for port in convert_to_list(field.data)]
        maximum = len(sw_model.port_names.split(','))
        for port in ports:
            if not 0 < port <= maximum:
                raise ValidationError(self.message.format(
                    port=port,
                    maximum=maximum,
                    model=sw_model.model
                    ))


class CheckVlans:
    def __init__(self, message=None, required_field=None):
        if not message:
            message = ('Номером влана может быть только число'
                       ' в диапазоне 1-4094')
        self.message = message
        self.required_field = required_field

    def __call__(self, form, field):
        try:
            if self.required_field:
                key, value = self.required_field
                if not form.data.get(key) == value:
                    return
            vlans = convert_to_list(field.data)
            if not vlans:
                raise ValueError
            for vlan in vlans:
                vlan = int(vlan)
                if not 1 <= vlan <= 4094:
                    raise ValueError
        except ValueError:
            raise ValidationError(self.message)


class CheckSingleVlan:
    def __init__(self, message=None, required_field=None):
        if not message:
            message = ('Номером влана может быть только число'
                       ' в диапазоне 1-4094')
        self.message = message
        self.required_field = required_field

    def __call__(self, form, field):
        try:
            if self.required_field:
                key, value = self.required_field
                if not form.data.get(key) == value:
                    return
            if not 1 <= int(field.data) <= 4094:
                raise ValueError
        except ValueError:
            raise ValidationError(self.message)


class CheckPortsOverlap():
    def __init__(self, message=None, required_field=None):
        if not message:
            message = (
                'Клиентские порты {client_ports} и текущие'
                ' пересекаются на портах: {overlapped_ports}'
                )
        self.message = message
        self.required_field = required_field

    def __call__(self, form, field):
        storage = StorageForMakeConfig.query.filter_by(
            user_id=current_user.id
            ).first()
        client_ports = set(convert_to_list(storage.client_ports))
        current_ports = set(convert_to_list(field.data))
        overlapped_ports = client_ports & current_ports
        if overlapped_ports:
            overlapped_ports = [
                port for port in sorted(overlapped_ports,
                                        key=(lambda x:int(x)))
                ]
            raise ValidationError(self.message.format(
                client_ports=storage.client_ports,
                overlapped_ports=','.join(overlapped_ports)
                ))



class MakeConfigForm1(FlaskForm):
    sw_model = SelectField('Модель коммутатора', coerce=int)
    mku_name = SelectField('МКУ', coerce=int)
    submit1 = SubmitField('Следующий шаг')

    def __init__(self, sw_model_choices,  mku_name_choices,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sw_model.choices = sw_model_choices
        self.mku_name.choices = mku_name_choices


class MakeConfigForm2(FlaskForm):
    hostname = StringField('Hostname', validators=[
        CheckHostname()
        ])
    ipaddress = StringField('IPv4', validators=[
        IPAddress(message='Неверный формат ip-адреса')
        ])
    netmask = StringField('MASK', validators=[CheckNetmask()])
    gateway = StringField('GW', validators=[
        IPAddress('Неверный формат ip-адреса'),
        CheckIPConnectivity()
        ])
    mng_vlan = StringField('MGMT_VLAN', validators=[CheckVlans()])
    client_ports = StringField(
        'Диапазон клиентских портов (например 1,3-24)',
        validators=[CheckPorts()])
    vlan_character = RadioField('Характер вланов', choices=[
        ('PCV','PCV'), ('single_vlan','Один влан на все порты')
        ], validators=[DataRequired(message='Неоходимо выбрать')],
           default='PCV')
    PCV_group = SelectField('Диапазон вланов PCV', coerce=int)
    pppoe_single_vlan = StringField(
        'Указать одиночный влан',
        validators=[CheckSingleVlan(required_field=('vlan_character',
                                                    'single_vlan'))])
    reset_2 = SubmitField('Начать заново')
    submit2 = SubmitField('Следующий шаг')

    def __init__(self, PCV_group_choices,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.PCV_group.choices = PCV_group_choices


class MakeConfigForm3(FlaskForm):
    switches_ports_uplink = StringField('Указать uplink порт',
                                        validators=[
                                            CheckPorts(),
                                            CheckPortsRange(),
                                            CheckPortsOverlap()
                                            ])
    switches_ports = StringField(
        'Порты для подключения других свитчей(в том числе uplink)',
        validators=[CheckPorts(),
                    CheckPortsRange(),
                    CheckPortsOverlap()]
        )
    switches_ports_vlans = StringField(
        ('Вланы на портах для подключения других свитчей'
         ' (можно добавить вланы по одному или диапазоном)'),
        validators=[CheckVlans()]
        )
    reset_3 = SubmitField('Начать заново')
    submit3 = SubmitField('Сгенерировать конфиг')

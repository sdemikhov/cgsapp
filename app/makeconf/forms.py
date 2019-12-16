from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, RadioField, SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired, IPAddress, Required
import ipaddress

from ..common_functions import convert_to_list


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


class MakeConfigForm1(FlaskForm):
    # SelectFields must get data from db. To do later
    sw_model = SelectField('Модель коммутатора', coerce=int)
    mku_name = SelectField('МКУ', coerce=int)
    submit1 = SubmitField('Следующий шаг')

    def __init__(self, sw_model_choices,  mku_name_choices,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sw_model.choices = sw_model_choices
        self.mku_name.choices = mku_name_choices


class MakeConfigForm2(FlaskForm):
    # must add validators
    hostname = StringField('Hostname', validators=[
        DataRequired()
        ])
    _forbidden_hostname_symbols = ['#', '>', '%', '!']
    ipaddress = StringField('IPv4', validators=[
        IPAddress(message='Неверный формат ip-адреса')
        ])
    netmask = StringField('MASK', validators=[CheckNetmask()])
    gateway = StringField('GW', validators=[
        IPAddress('Неверный формат ip-адреса'),
        CheckIPConnectivity()
        ])
    mng_vlan = StringField('MGMT_VLAN', validators=[CheckVlans()])
    client_ports = StringField('Диапазон клиентских портов (например 1,3-24)',
                               validators=[CheckPorts()])
    vlan_character = RadioField('Характер вланов', choices=[
        ('PCV','PCV'), ('single_vlan','Один влан на все порты')
        ], validators=[Required(message='Неоходимо выбрать')])
    PCV_group = SelectField('Диапазон вланов PCV', coerce=int)
    pppoe_single_vlan = StringField('Указать одиночный влан', validators=[
        CheckVlans(required_field=('vlan_character', 'single_vlan'))
        ])
    reset_2 = SubmitField('Начать заново')
    submit2 = SubmitField('Следующий шаг')

    def __init__(self, PCV_group_choices,  *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.PCV_group.choices = PCV_group_choices

    def validate_hostname(self, field):
        for symbol in self._forbidden_hostname_symbols:
            if symbol in field.data:
                msg = (
                f'запрещены символы '
                f'{", ".join(self._forbidden_hostname_symbols)}'
                )
                raise ValidationError(msg)


class MakeConfigForm3(FlaskForm):
    switches_ports_uplink = StringField('Указать uplink порт',
                                        validators=[CheckPorts()])
    switches_ports = StringField('Порты для подключения других свитчей(в том числе uplink)',
                                 validators=[CheckPorts()])
    switches_ports_vlans = StringField('Вланы на портах для подключения других свитчей',
                                        validators=[CheckVlans()])
    reset_3 = SubmitField('Начать заново')
    submit3 = SubmitField('Сгенерировать конфиг')

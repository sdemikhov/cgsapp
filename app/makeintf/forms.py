from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SubmitField
from wtforms.validators import Regexp, IPAddress, Optional

from ..makeconf.forms import CheckSingleVlan, CheckHostname


class MakeIntfForm1(FlaskForm):
    intf_type = RadioField('Выберите тип интерфейса')
    submit = SubmitField('Следующий шаг')

    def __init__(self, intf_type_choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.intf_type.choices = intf_type_choices


class MakeIntfForm2(FlaskForm):
    lag = StringField('LAG (доступные лаги 1,11,12,13,14)', validators=[
                                Regexp('^1[1234]?$',
                                0,
                                'доступные лаги 1,11,12,13,14')
                                ])
    outer_vlan = StringField('Внешний влан',
                             validators=[CheckSingleVlan()])
    inner_vlan = StringField('Внутренний влан',
                             validators=[CheckSingleVlan()])
    description = StringField('Description',
                              validators=[CheckHostname()])
    ip = StringField('IP-адрес', validators=[IPAddress()])
    reset = SubmitField('Начать заново')
    submit = SubmitField('Создать интерфейс')

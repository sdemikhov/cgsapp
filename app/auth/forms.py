from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(FlaskForm):
    email = StringField('E-mail',
                        validators=[DataRequired(), Length(1,64), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class RegistrationForm(FlaskForm):
    email = StringField('E-mail',
                        validators=[DataRequired(), Length(1,64), Email()])
    first_name = StringField('Имя',
                             validators=[DataRequired(), Length(1,64), 
                             Regexp('^[А-Яа-я]*$',
                             0,
                             'поле может содержать только буквы')])

    last_name = StringField('Фамилия',
                             validators=[DataRequired(), Length(1,64), 
                             Regexp('^[А-Яа-я]*$',
                             0,
                             'поле может содержать только буквы')])
                        
    password = PasswordField('Пароль',
                             validators=[
                    DataRequired(),
                    EqualTo('password2', 'пароли должны совпадать')
                    ])
    password2 = PasswordField('Подтвердите пароль',
                              validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('E-mail уже используется')

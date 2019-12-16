from flask_wtf import FlaskForm
from wtforms import (SelectField, SelectMultipleField, SubmitField,
                     DateTimeField)
from wtforms import ValidationError


class ManageUsersForm(FlaskForm):
    registration = DateTimeField(
        'Изменить дату окончания регистрации (гггг-мм-дд чч:мм:сс):',
        format='%Y-%m-%d %H:%M:%S'
        )
    users = SelectMultipleField('Выберите учетные записи:',
                                coerce=int)
    edit = SelectField('Действие над выбранными записями:',
                       coerce=int)
    submit = SubmitField('Выполнить')

    def __init__(self, users_choices,  edit_choices,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.users.choices = users_choices
        self.edit.choices = [(0, 'Ничего не делать')] + edit_choices

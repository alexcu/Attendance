from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired


class NameForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])


class LoginForm(FlaskForm):
    user_id = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

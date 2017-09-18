from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Optional


class NameForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Email(), Optional()])


class LoginForm(FlaskForm):
    user_id = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class AddSubjectForm(FlaskForm):
    subcode = StringField('Subject Code', validators=[DataRequired()])
    subname = StringField('Subject Name', validators=[DataRequired()])


class StudentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    studentcode = StringField('Student Code', validators=[DataRequired()])
    email = StringField('Email', validators=[Email(), Optional()])


class TimeslotForm(FlaskForm):
    day = StringField('Day', validators=[DataRequired()])
    time = StringField('Time', validators=[DataRequired()])

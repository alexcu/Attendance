from wtforms import *
from wtforms.validators import *


class NameForm(Form):
    name = StringField('Name', validators=[DataRequired()])

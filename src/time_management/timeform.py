from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, IntegerField
from wtforms.validators import InputRequired, NumberRange

class TimeForm(FlaskForm):
    min_minutes = 1
    max_minutes = 1440

    minutes_field = IntegerField("Number of Minutes", default=min_minutes, validators=[InputRequired(),NumberRange(min=min_minutes, max=max_minutes)])
    action_field = SelectField('Action Type', choices = [('used', 'used'), ('topup', 'topup')], validate_choice=True)

    submit = SubmitField('Submit')

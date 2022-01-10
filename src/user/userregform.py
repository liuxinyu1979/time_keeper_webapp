from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, EqualTo, ValidationError, Length

class UserRegistrationForm(FlaskForm):
    min_name_len = 3
    max_name_len = 64

    user_name = StringField("User Name", 
                validators=[InputRequired(), 
                    Length(min=min_name_len, max=max_name_len, message=f"user name length must be between {min_name_len} and {max_name_len}")])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    password2 = PasswordField('Repeat Password', validators=[InputRequired(), EqualTo('password', message="password must match")])
    submit = SubmitField('Register')

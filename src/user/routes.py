from flask import Flask, render_template, request
from user.user import User
from user.userregform import UserRegistrationForm

from main import app


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        return User().signup()

    user_name = None
    registration_form = UserRegistrationForm()
    if registration_form.validate_on_submit():
        user_name = registration_form.user_name.data
        registration_form.user_name.data = ''

    return render_template("registration.html", user_name = user_name, registration_form = registration_form)

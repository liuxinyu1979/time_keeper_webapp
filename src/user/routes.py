from flask import Flask, render_template, request
from user.user import User
from user.userregform import UserRegistrationForm

from main import app


# Obviously when user enter url http://<base url>/registration, we will render the form since the request.method == 'GET'
# when request.method is POST, we will pass in the form data to create the user object
@app.route('/registration', methods=['GET', 'POST'])
def registration():
    registration_form = UserRegistrationForm()
    if request.method == 'POST' and registration_form.validate():
        return User().signup()

    user_name = None
    if registration_form.validate_on_submit():
        user_name = registration_form.user_name.data
        registration_form.user_name.data = ''

    return render_template("registration.html", user_name = user_name, registration_form = registration_form)

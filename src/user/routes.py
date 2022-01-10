from flask import Flask, render_template, request
from user.user import User
from user.userregform import UserRegistrationForm
from werkzeug.security import generate_password_hash
from main import app, account_mgmt


# Obviously when user enter url http://<base url>/registration, we will render the form since the request.method == 'GET'
# when request.method is POST, we will pass in the form data to create the user object
@app.route('/registration', methods=['GET', 'POST'])
def registration():
    registration_form = UserRegistrationForm()
    if request.method == 'POST' and registration_form.validate():
        password_hashed = generate_password_hash(registration_form.password.data)
        if account_mgmt.acc_name_exist(registration_form.user_name.data):
            registration_form.user_name.errors.append("user already exists")
            return render_template("registration.html", registration_form = registration_form)
        return account_mgmt.signup(registration_form.user_name.data, registration_form.email.data, password_hashed)

    user_name = None
    if registration_form.validate_on_submit():
        user_name = registration_form.user_name.data
        registration_form.user_name.data = ''

    return render_template("registration.html", registration_form = registration_form)

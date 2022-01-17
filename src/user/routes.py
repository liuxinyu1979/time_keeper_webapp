from flask import Flask, render_template, request
from user.user import User
from user.userregform import UserRegistrationForm, UserLoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from main import app, account_mgmt

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user


login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class UserAccount(UserMixin):

    def __init__(self, user):

        self.name = user['name']
        self.email = user['email']
        self.passwd = user['password']

    def is_authenticated(self):
        return True

    def is_active(self):   
        return True           

    def is_anonymous(self):
        return False          

    def get_id(self):         
        return self.name




@login_manager.user_loader
def load_user(user_id):
    user = account_mgmt.get_user(user_id)
    if user == None:
        return None
    user_acc = UserAccount(user)
    return user_acc



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
        user = account_mgmt.signup(registration_form.user_name.data, registration_form.email.data, password_hashed)
        acc = UserAccount(user)
        login_user(acc)
        # once signup is complete, 
        return render_template("home.html")

    user_name = None
    if registration_form.validate_on_submit():
        user_name = registration_form.user_name.data
        registration_form.user_name.data = ''

    return render_template("registration.html", registration_form = registration_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = UserLoginForm()
    if request.method == 'POST' and login_form.validate():
        usr =  account_mgmt.get_user(login_form.user_name.data)

        if usr is not None and check_password_hash(usr['password'],login_form.password.data):
            acc = UserAccount(usr)
            login_user(acc)

            # return render_template("home.html", user_name = login_form.user_name.data)
            return render_template("home.html")
        else:
            login_form.user_name.errors.append("user does not exists")
    return render_template("login.html", login_form=login_form)
    
@app.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    return render_template("index.html")
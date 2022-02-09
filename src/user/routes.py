from flask import Flask, render_template, request,jsonify
from user.user import User
from user.userregform import UserRegistrationForm, UserLoginForm, AccountInfoForm, AccountSecretForm
from werkzeug.security import generate_password_hash, check_password_hash
from main import app, account_mgmt, time_keeper_dao

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class UserAccount(UserMixin):

    def __init__(self, user):

        self.name = user['name']
        self.email = user['email']
        self.passwd = user['password']

    def get_email(self):
        return self.email
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


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def account_profile():
    account_info_form = AccountInfoForm()
    user_name = current_user.get_id()
    account_info_form.user_name.data = user_name
    usr =  account_mgmt.get_user(user_name)
    acc = UserAccount(usr)


    if request.method == 'GET':
        account_info_form.email.data = acc.get_email() 
        render_template("updateprofile.html", account_info_form=account_info_form)

    if request.method == 'POST':
        if account_info_form.validate():
            email = account_info_form.email.data
            status, err = account_mgmt.update_account_info(user_name, email)
            if status == False:
                account_info_form.user_name.errors.append(err["error"])
            else:
                account_info_form.user_name.errors.append("account info update successful")
            return render_template("updateprofile.html",account_info_form=account_info_form)
        
    return render_template("updateprofile.html", account_info_form=account_info_form)

@app.route('/secret', methods=['GET', 'POST'])
@login_required
def account_secret():
    account_sec_form = AccountSecretForm()
    user_name = current_user.get_id()
    account_sec_form.user_name.data = user_name
    usr =  account_mgmt.get_user(user_name)
    acc = UserAccount(usr)

    if request.method == 'GET':
        account_sec_form.password.data = ""
        account_sec_form.password2.data = ""
        render_template("updatesecret.html", account_secret_form=account_sec_form)

    if request.method == 'POST':
        if account_sec_form.validate():
            password_hashed = generate_password_hash(account_sec_form.password.data)
            status, err = account_mgmt.update_account_secret(user_name, password_hashed)
            if status == False:
                account_sec_form.user_name.errors.append(err["error"])
            else:
                account_sec_form.user_name.errors.append("account secret update successful")
            return render_template("updatesecret.html",account_secret_form=account_sec_form)
        
    return render_template("updatesecret.html", account_secret_form=account_sec_form)






from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    usr =  account_mgmt.get_user(username)
    if usr == None:
        return False

    if check_password_hash(usr['password'],password):
        return True
    return False


# login auth via api
@app.route("/api/v1.0/user", methods=['GET'])
@auth.login_required
def get_user_api():
    user_name = auth.current_user()
    return jsonify(
        {
            "user_name":user_name, 
            "topup_minutes":time_keeper_dao.minutes_toppedup(user_name), 
            "used_minutes": time_keeper_dao.minutes_used(user_name), 
            "remaining_minutes": time_keeper_dao.minutes_left(user_name)
        }), 200


'''
Test endpoints
'''
# login auth via api
@app.route("/api/v1.0/testuser", methods=['GET'])
@auth.login_required
def get_test_user_api():

    return "testuser", 200



'''
End of test endpoints
'''

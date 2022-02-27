from flask_login import UserMixin

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

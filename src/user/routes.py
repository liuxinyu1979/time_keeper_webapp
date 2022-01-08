from flask import Flask
from user.user import User

from main import app


@app.route("/user/signup", methods=['GET'])
def signup():
    return User().signup()

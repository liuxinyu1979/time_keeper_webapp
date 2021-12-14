from flask import Flask, render_template
from config import DevConfig


app = Flask(__name__)
app.config.from_object(DevConfig)

@app.route('/')
def home():
    return f"<h1>Hello world</h1>"

@app.route('/<string:user_name>')
def greeting(user_name):
    return f"<h1>Hello {user_name}</h1>"

if __name__ == '__main__':
    app.run

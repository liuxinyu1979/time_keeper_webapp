from flask import Flask, render_template
from config import DevConfig
from flask_pymongo import PyMongo


app = Flask(__name__)
app.config.from_object(DevConfig)
app.config["MONGO_URI"] = "mongodb://localhost:27017/testtimedb"
mongo = PyMongo(app)

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/<string:user_name>')
def greeting(user_name):
    return f"<h1>Hello {user_name}</h1>"

@app.route('/admin_actions', methods=['GET'])
def adminactions():
    admin_action = mongo.db.admin.find_one()
    return f"<h1>{admin_action['action']}</h1> <h1>{admin_action['datetime']}</h1>"



if __name__ == '__main__':
    app.run
    
    

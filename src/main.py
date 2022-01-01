from time import time
from flask import Flask, render_template,jsonify
from TimeKeeperDao import TimeKeeperDao
from config import DevConfig
from flask_pymongo import PyMongo
from TimeKeeperDao import TimeKeeperDao


app = Flask(__name__)
app.config.from_object(DevConfig)
app.config["MONGO_URI"] = "mongodb://localhost:27017/testtimedb"
app.config["MONGODB_CONNECTION_TIMEOUT_MS"] = 100
time_keeper_dao = TimeKeeperDao(app)
if time_keeper_dao.db_exist == False:
    print("db not exist")
    exit()

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/<string:user_name>')
def greeting(user_name):
    return f"<h1>Hello {user_name}</h1>"

@app.route('/test_admin_actions', methods=['GET'])
def testadminactions():
    admin_action = time_keeper_dao.admin_action_get_one()
    if admin_action == None:
        return f"<h1>admin page</h1>"

    return f"<h1>{admin_action['action']}</h1> <h1>{admin_action['datetime']}</h1>"

# For the two admin graphs
@app.route('/retrieve_admin_stats', methods=['GET'])
def retrieve_admin_stats():
    success_flags, date_range, success_flags_hit_count, actions, actions_hit_count  = time_keeper_dao.retrieve_admin_stat()
    resp = {
        "date_range": date_range,
        "attempt_success": success_flags[0],
        "attempt_failed": success_flags[1],
        actions[0]:actions_hit_count[0],
        actions[1]:actions_hit_count[1],
        actions[2]:actions_hit_count[2]
    }
    ss = jsonify(resp)
    print(ss)
    return ss



if __name__ == '__main__':
    app.run
    
    

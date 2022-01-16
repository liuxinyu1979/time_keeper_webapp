from time import time
from flask import Flask, render_template,jsonify
from timekeeperdao import TimeKeeperDao
from user.user import User

from config import DevConfig
from flask_pymongo import PyMongo
import plotgraphs

app = Flask(__name__)
app.config.from_object(DevConfig)
app.config["MONGO_URI"] = "mongodb://localhost:27017/testtimedb"
app.config["MONGODB_CONNECTION_TIMEOUT_MS"] = 100
app.config["SECRET_KEY"] = "my secret key"
account_mgmt = User(app)

# the routes module is going to import the flask app object, so keep the import below app = Flask...
from user import routes

time_keeper_dao = TimeKeeperDao(app)
if time_keeper_dao.db_exist == False:
    print("db not exist")
    exit()

@app.route('/home')
@app.route('/home/<user_name>')
def home(user_name=None):
    print(f"user {user_name} is called")
    return render_template("home.html", user_name = user_name)


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/show_admin_graphs', methods=['GET'])
def show_admin_graphs():
    success_flags, date_range, success_flags_hit_count, action_names, actions_hit_count  = time_keeper_dao.retrieve_admin_stat()

    action_imgs = []
    action_imgs.append(plotgraphs.heatmap_plot_img(date_range, success_flags, success_flags_hit_count, "Admin password attempt heatmap"))
    action_imgs.append(plotgraphs.heatmap_plot_img(date_range, action_names, actions_hit_count, "Admin actions heatmap"))
    # display two images in one row in full screen
    return render_template("graphs.html", admin_action_graphs=action_imgs, graph_count=len(action_imgs), cols = 2)


@app.route('/show_time_bucket_graphs', methods=['GET'])
def show_time_bucket_graphs():
    date_range, used, added, ampm, hrs, hit_count = time_keeper_dao.retrieve_for_time_stat(0,1)

    time_bucket_imgs = []

    time_bucket_imgs.append(plotgraphs.time_bucket_double_bar_plot_img(date_range, used, added, 'minutes', 'used minutes', "dates vs minutes", 'minutes used'))
    time_bucket_imgs.append(plotgraphs.time_bucket_bar_plot_img(date_range, used, 'used minutes', "used minutes per day", 'minutes used'))
    time_bucket_imgs.append(plotgraphs.time_bucket_bar_plot_img(date_range, added, 'added minutes', "Added minutes per day", 'minutes added'))
    time_bucket_imgs.append(plotgraphs.heatmap_plot_img(hrs, ampm, hit_count, "Admin actions heatmap"))
    # display two images in one row in full screen
    return render_template("graphs.html", admin_action_graphs=time_bucket_imgs, graph_count=len(time_bucket_imgs), cols = 2)



'''
Test functions start
'''

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
        "attempt_flags": success_flags,
        actions[0]:actions_hit_count[0],
        actions[1]:actions_hit_count[1],
        actions[2]:actions_hit_count[2]
    }
    ss = jsonify(resp)
    print(ss)
    return ss

# retrieve all time graphs
@app.route('/retrieve_time_stats', methods=['GET'])
def retrieve_time_stats():
    date_range, used, added, ampm, hrs, hit_count = time_keeper_dao.retrieve_for_time_stat(0,1)
    resp = {
        "date_range": date_range,
        "used": used,
        "added": added,
        "hours":hrs,
        "ampm": ampm,
        "am_hit_count": hit_count[0],
        "pm_hit_count": hit_count[1]
    }
    ss = jsonify(resp)
    print(ss)
    return ss    
###################################



if __name__ == '__main__':
    app.run
    
    

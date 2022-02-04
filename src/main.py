from datetime import timedelta
from time import time
from flask import Flask, render_template,jsonify, request
# from timekeeperdao_ import TimeKeeperDao
from time_management.timekeeperdao import TimeKeeperDao
from user.user import User

from config import DevConfig
from flask_pymongo import PyMongo
import plotgraphs
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(DevConfig)
app.config["MONGO_URI"] = "mongodb://localhost:27017/testtimedb"
app.config["MONGODB_CONNECTION_TIMEOUT_MS"] = 100
# python -c 'import secrets; print(secrets.token_hex())'
app.config["SECRET_KEY"] = "my secret key"
# relogin after 30 minutes
app.permanent_session_lifetime = timedelta(minutes=30)
account_mgmt = User(app)
time_keeper_dao = TimeKeeperDao(app)

# the routes module is going to import the flask app object, so keep the import below app = Flask...
from user import routes
from time_management import routes
from flask_login import current_user, login_required

if time_keeper_dao.db_exist == False:
    print("Log: db not exist")
    exit()

@app.route('/home')
@app.route('/home/<user_name>')
@login_required
def home(user_name=None):
    return render_template("home.html", user_name = user_name)


@app.route('/')
def index():
    if current_user.get_id() == None:
        return render_template("index.html")

    return render_template("home.html")

import tempfile
import os
@app.route('/time_file_upload', methods=['GET', 'POST'])
@login_required
def upload_time_file():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        upload_file_name = secure_filename(request.files['file'].filename)
        tmpdir = tempfile.gettempdir()
        tmp_file = os.path.join(tmpdir, upload_file_name)
        uploaded_file.save(tmp_file)
        user = current_user.get_id()
        time_file_upload_success = time_keeper_dao.update_db_by_import(tmp_file, user)
            
        remaining_time = time_keeper_dao.minutes_left(user)
        return render_template("/timeFileUploadResult.html", file_name=upload_file_name, time_file_upload_success=time_file_upload_success, remaining_time=remaining_time)

    return render_template('timeFileUpload.html')


@app.route('/show_admin_graphs', methods=['GET'])
@login_required
def show_admin_graphs():
    success_flags, date_range, success_flags_hit_count, action_names, actions_hit_count  = time_keeper_dao.retrieve_admin_stat(current_user.get_id())

    action_imgs = []
    action_imgs.append(plotgraphs.heatmap_plot_img(date_range, success_flags, success_flags_hit_count, "Admin password attempt heatmap"))
    action_imgs.append(plotgraphs.heatmap_plot_img(date_range, action_names, actions_hit_count, "Admin actions heatmap"))
    # display two images in one row in full screen
    return render_template("graphs.html", admin_action_graphs=action_imgs, graph_count=len(action_imgs), cols = 2)


@app.route('/show_time_bucket_graphs', methods=['GET'])
@login_required
def show_time_bucket_graphs():
    date_range, used, added, ampm, hrs, hit_count = time_keeper_dao.retrieve_for_time_stat(0,1, current_user.get_id())

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
@login_required
def greeting(user_name):
    return f"<h1>Greeting: Hello {user_name}</h1>"

@app.route('/test_admin_actions', methods=['GET'])
@login_required
def testadminactions():
    admin_action = time_keeper_dao.admin_action_get_one()
    if admin_action == None:
        return f"<h1>admin page</h1>"

    return f"<h1>{admin_action['action']}</h1> <h1>{admin_action['datetime']}</h1>"

# For the two admin graphs
@app.route('/retrieve_admin_stats', methods=['GET'])
@login_required
def retrieve_admin_stats():
    success_flags, date_range, success_flags_hit_count, actions, actions_hit_count  = time_keeper_dao.retrieve_admin_stat(current_user.get_id())
    resp = {
        "date_range": date_range,
        "attempt_flags": success_flags,
        actions[0]:actions_hit_count[0],
        actions[1]:actions_hit_count[1],
        actions[2]:actions_hit_count[2]
    }
    ss = jsonify(resp)
    return ss

# retrieve all time graphs
@app.route('/retrieve_time_stats', methods=['GET'])
@login_required
def retrieve_time_stats():
    date_range, used, added, ampm, hrs, hit_count = time_keeper_dao.retrieve_for_time_stat(0,1, current_user.get_id())
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
    return ss    
'''
End of test endpoints
'''
###################################



if __name__ == '__main__':
    app.run
    
    

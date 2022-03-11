
from time import time
from flask import Flask, current_app, render_template,jsonify, request
from src import create_app

from time_management.timekeeperdao import TimeKeeperDao
from user.user import User

from config import DevConfig
from flask_pymongo import PyMongo
import plotgraphs
from werkzeug.utils import secure_filename

app, mongo_client = create_app(None)
if app == None:
    print("Log: unable to create application or mongo connection, exiting")
    exit()

# Must create time_keeper_do before account_mgmt because time_keeper_dao makes sure records db exists. 
time_keeper_dao = TimeKeeperDao(mongo_client)
account_mgmt = User(mongo_client=mongo_client, time_keeper_dao=time_keeper_dao)

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
    # we first save it to tmp, and then parse that tmp file
    if request.method == 'POST':
        time_file_upload_success = False
        uploaded_file = request.files['file']
        upload_file_name = secure_filename(request.files['file'].filename)
        file_ext = os.path.splitext(upload_file_name)[1]
        user = current_user.get_id()
        if file_ext in current_app.config['UPLOAD_EXTENSIONS']:
            tmpdir = tempfile.gettempdir()
            tmp_file = os.path.join(tmpdir, upload_file_name)
            uploaded_file.save(tmp_file)
            time_file_upload_success = time_keeper_dao.update_db_by_import(tmp_file, user)
            
        remaining_time = time_keeper_dao.minutes_left(user)
        return render_template("timeManagementResult.html", graph_url_name="Upload time file result", file_name=upload_file_name, time_file_upload_success=time_file_upload_success, remaining_time=remaining_time)

    return render_template('timeFileUpload.html', graph_url_name="Upload time file")


@app.route('/show_admin_graphs', methods=['GET'])
@login_required
def show_admin_graphs():
    success_flags, date_range, success_flags_hit_count, action_names, actions_hit_count  = time_keeper_dao.retrieve_admin_stat(current_user.get_id())

    action_imgs = []
    action_imgs.append(plotgraphs.heatmap_plot_img(date_range, success_flags, success_flags_hit_count, "Admin password attempt heatmap"))
    action_imgs.append(plotgraphs.heatmap_plot_img(date_range, action_names, actions_hit_count, "Admin actions heatmap"))
    # display two images in one row in full screen
    return render_template("graphs.html", graph_url_name="Admin graphs", admin_action_graphs=action_imgs, graph_count=len(action_imgs), cols = 2)


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
    return render_template("graphs.html", graph_url_name="Time graphs", admin_action_graphs=time_bucket_imgs, graph_count=len(time_bucket_imgs), cols = 2)

@app.route('/about.QooQoo', methods=['GET'])
@login_required
def about_page():

    return render_template("about.html")


# to enable ssl_context for on-the-fly certificates, run flask run --cert=adhoc 
if __name__ == '__main__':
    app.run(ssl_context='adhoc')
    
    

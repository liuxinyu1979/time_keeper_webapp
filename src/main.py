from time import time
from flask import Flask, render_template,jsonify
from TimeKeeperDao import TimeKeeperDao
from config import DevConfig
from flask_pymongo import PyMongo
from TimeKeeperDao import TimeKeeperDao

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO



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
    return render_template("home.html", admin_action_graph="home")

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

@app.route('/show_admin_graphs', methods=['GET'])
def show_admin_graphs():
    success_flags, date_range, success_flags_hit_count, actions, actions_hit_count  = time_keeper_dao.retrieve_admin_stat()
    resp = {
        "date_range": date_range,
        "attempt_success": success_flags[0],
        "attempt_failed": success_flags[1],
        actions[0]:actions_hit_count[0],
        actions[1]:actions_hit_count[1],
        actions[2]:actions_hit_count[2]
    }

   # remove the year from yyyy-mm-dd
    dr = [d[5:] for d in date_range]

    plt.rcParams.update({'font.size': 5})
    plt.style.use('grayscale')

    fig = Figure()
    axs5 = fig.add_subplot(1, 2, 1)
    # Note that even in the OO-style, we use `.pyplot.figure` to create the figure.
    # fig, (axs5, axs6)  = plt.subplots(1,2)  # Create a figure and an axes.
 
    # remove the year from yyyy-mm-dd
    success_flags_date_range = [d[5:] for d in date_range]
    axs5.imshow(success_flags_hit_count, cmap = 'Greens')
    # Show all ticks and label them with the respective list entries
    axs5.set_xticks(np.arange(len(success_flags_date_range)), labels=success_flags_date_range)
    axs5.set_yticks(np.arange(len(success_flags)), labels=success_flags)
    # Loop over data dimensions and create text annotations.
    for i in range(len(success_flags)):
        for j in range(len(success_flags_date_range)):
            text = axs5.text(j, i, success_flags_hit_count[i][j],
                        ha="center", va="center", color="r")
    axs5.set_title("Admin password attempt heatmap")  # Add a title to the axes.
    axs5.legend()  # Add a legend.    
    
    axs6 = fig.add_subplot(1, 2, 2)
    axs6.imshow(actions_hit_count, cmap = 'Greens')
    # Show all ticks and label them with the respective list entries
    axs6.set_xticks(np.arange(len(success_flags_date_range)), labels=success_flags_date_range)
    axs6.set_yticks(np.arange(len(actions)), labels=actions)
    # Loop over data dimensions and create text annotations.
    for i in range(len(actions)):
        for j in range(len(success_flags_date_range)):
            text = axs6.text(j, i, actions_hit_count[i][j],
                        ha="center", va="center", color="r")
    axs6.set_title("Admin actions heatmap")  # Add a title to the axes.
    axs6.legend()  # Add a legend.    
    axs5.set_xticklabels(axs5.get_xticklabels(), rotation=315, ha='right')
    axs6.set_xticklabels(axs6.get_xticklabels(), rotation=315, ha='right')

    # fig.tight_layout()
    # Convert plot to PNG image
    pngImage = BytesIO()
    FigureCanvas(fig).print_png(pngImage)
    
    # Encode PNG image to base64 string
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')
    
    return render_template("home.html", admin_action_graph=pngImageB64String)




# retrieve all time graphs
@app.route('/retrieve_time_stats', methods=['GET'])
def retrieve_time_stats():
    date_range, used, added, ampm, hrs, hit_count = time_keeper_dao.retrieve_for_time_stat(0,1)
    resp = {
        "date_range": date_range,
        "used": used,
        "added": added,
        "hours":hrs,
        "am": hit_count[0],
        "pm": hit_count[1]
    }
    ss = jsonify(resp)
    print(ss)
    return ss


if __name__ == '__main__':
    app.run
    
    

import json
from flask import Flask, render_template, request,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from main import app, account_mgmt, time_keeper_dao
from datetime import datetime
from time_management.timeform import TimeForm

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

import tempfile
import os
from werkzeug.utils import secure_filename

@app.route('/api/v1.0/time_file', methods=['POST'])
@auth.login_required
def post_time_file():
    time_file_upload_success = False
    uploaded_file = request.files['file']
    upload_file_name = secure_filename(request.files['file'].filename)
    file_ext = os.path.splitext(upload_file_name)[1]
    user = auth.current_user()
    resp_status = 200
    resp_msg = "upload successful"
    if file_ext in app.config['UPLOAD_EXTENSIONS']:
        tmpdir = tempfile.gettempdir()
        tmp_file = os.path.join(tmpdir, upload_file_name)
        uploaded_file.save(tmp_file)
        time_file_upload_success = time_keeper_dao.update_db_by_import(tmp_file, user)
        if not time_file_upload_success:
            resp_status = 400
            resp_msg = "File format error"
    else:
        resp_status = 400
        resp_msg = f"Upload failed, only {app.config['UPLOAD_EXTENSIONS']} file extension allow"
    remaining_time = time_keeper_dao.minutes_left(user)

    resp = {
        "status": time_file_upload_success,
        "remaining_time": remaining_time, 
        "message": resp_msg
    }
    return jsonify(resp), resp_status


@app.route('/api/v1.0/admin_action', methods=['POST'])
@auth.login_required
def record_admin_actions():
    req_body = request.get_json(force=True)
    err_msg = ""
    if 'action' not in req_body or "is_successful" not in req_body:
        err_msg = "request body missing minutes count"

    if len(err_msg) > 0:
        return jsonify({"error":err_msg}), 400
    admin_action = req_body['action']
    is_successful = bool(req_body['is_successful']) 

    has_no_err, msg = time_keeper_dao.record_admin_action(admin_action, is_successful, auth.current_user())

    if not has_no_err:
        return jsonify({"error":msg}), 400
    
    return jsonify({}), 200


@app.route('/api/v1.0/minutes', methods=['POST'])
@auth.login_required
def add_minutes():
    req_body = request.get_json(force=True)

    type_vals = {'added','used'}

    err_msg = ""
    if 'minutes' not in req_body or 'type' not in req_body:
        err_msg = "request body must have minutes and type"
    elif type(req_body['minutes']) != int or req_body['minutes']  <= 0 or req_body['type'] not in type_vals:
        err_msg = "minutes value must be greater than 0 and type must be either added or used"
    
    if len(err_msg) > 0:
        return jsonify({"error":err_msg}), 400
    minutes_val = int(req_body['minutes'])
    
    value = {} 
    err = ""
    if req_body['type'] == 'added':
        value, err = time_keeper_dao.record_minutes_added(minutes_val, auth.current_user())
    else: # type == used
        value, err = time_keeper_dao.record_minutes_used(minutes_val, auth.current_user())
        
    if len(err) > 0:
        return jsonify(err), 400
    
    return jsonify(value), 200

@app.route('/api/v1.0/minutes', methods=['GET'])
@auth.login_required
def get_minutes():
    params = request.args.to_dict()
    type_vals = {'added','used'}
    if params == None or len(params) != 2 or 'type' not in params or 'date' not in params or params['type'] not in type_vals or len(params['date']) != 10:
        return {"error": "invalid parameter, correct type is ?type=[added|used]&date=[YYYY-MM-DD]"}, 400
    dt = None
    try:
        dt = datetime.fromisoformat(params['date'])
    except ValueError as e:
        return jsonify({"error": "invalid parameter, correct type is ?type=[added|used]&date=[YYYY-MM-DD]"}), 400
    k = 'minutesAdded' if params['type'] == 'added' else 'minutesUsed'

    records, err = time_keeper_dao.get_minutes_in_db(auth.current_user(), dt)

    if len(err) > 0:
        return jsonify({"error":"Not found"}), 404
    if records == None:
        return jsonify({params['type']:[]}), 200
    return jsonify({params['type']:records[k]}), 200


@app.route("/api/v1.0/get_time_stats")
@auth.login_required
def get_time_stats():
    date_range, used, added, ampm, hrs, hit_count = time_keeper_dao.retrieve_for_time_stat(0,1, auth.current_user())
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

@app.route("/api/v1.0/get_admin_stats")
@auth.login_required
def get_admin_stats():
    success_flags, date_range, success_flags_hit_count, actions, actions_hit_count  = time_keeper_dao.retrieve_admin_stat(auth.current_user())
    resp = {
        "date_range": date_range,
        "attempt_labels": success_flags,
        success_flags[0]:success_flags_hit_count[0],
        success_flags[1]:success_flags_hit_count[1],
        "action_labels":actions,
        actions[0]:actions_hit_count[0],
        actions[1]:actions_hit_count[1],
        actions[2]:actions_hit_count[2]
    }
    ss = jsonify(resp)
    return ss


@app.route('/specify_time', methods=['GET', 'POST'])
@auth.login_required
def specify_time():
    time_upload_form = TimeForm()
    if request.method == 'POST' and time_upload_form.validate():
        user_name = auth.current_user()
        input_minutes = time_upload_form.minutes_field.data
        input_action = time_upload_form.action_field.data
        print(user_name, input_minutes, input_action)
        # add to both records collection and log collection
        # we can direct to graphs 
        return render_template("home.html")

    if time_upload_form.validate_on_submit():
        time_upload_form.minutes_field.data= 1

    return render_template("uploadtime.html", time_upload_form = time_upload_form)
from flask import Flask, render_template, request,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from main import app, account_mgmt, time_keeper_dao


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


@app.route('/api/v1.0/minutes', methods=['POST'])
@auth.login_required
def add_minutes():
    req_body = request.get_json(force=True)
    err_msg = ""
    if 'minutes' not in req_body:
        err_msg = "request body missing minutes count"
    elif type(req_body['minutes']) != int or req_body['minutes']  <= 0:
        err_msg = "minutes value must be greater than 0"
    
    if len(err_msg) > 0:
        return err_msg, 400
    
    minutes_val = req_body['minutes']

    err, status = time_keeper_dao.topup_minutes_in_db(minutes_val, auth.current_user())
    if status == False:
        return err, 400
    
    return "", 200


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
    print(ss)
    return ss

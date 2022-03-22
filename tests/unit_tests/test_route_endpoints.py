from pytest_mock import mocker
from time_management.timekeeperdao import TimeKeeperDao
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from user.user import User
import mongomock
import json

# mock_app = None
# mock_mongo_client = None
# mocker = None
def get_mocked_collections():
    record_collection = mongomock.MongoClient().db.records
    admin_collection = mongomock.MongoClient().db.admin
    import_collection = mongomock.MongoClient().db.imports
    accounts_collection = mongomock.MongoClient().db.accounts

    return record_collection, admin_collection, import_collection, accounts_collection

def get_mocked_and_patched_collections(mocker):

    record_collection, admin_collection, import_collection, accounts_collection = get_mocked_collections()
    mocker.patch('flask_pymongo.wrappers.Database.list_collection_names', return_value=["records", "admin", "imports", "accounts"])
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_records_collection', return_value=record_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_imports_collection', return_value=import_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_admin_collection', return_value=admin_collection)
    mocker.patch('user.user.User.get_accounts_collection', return_value=accounts_collection)
    
    datetime_tmp = datetime.strptime("2021-11-24", '%Y-%m-%d')
    timestamp_part = {"hr":0, "minute": 0, "second": 0}
    record_collection.insert_one({"datetime":datetime_tmp, "user":"unittest", "minutesAdded":[35], "minutesUsed":[0],'minutesUsedTimeStamp':timestamp_part})
    admin_collection.insert_one({"datetime":datetime_tmp, "user":"unittest", "action":"Unpause", "is_success":True})
    import_collection.insert_one({"user":"unittest", "logline":"2022-02-14,topup,1"})
    dt = datetime.fromtimestamp(0)
    accounts_collection.insert_one({"name": "unittest","email": "test@test.com","password": generate_password_hash("123"), "created_on":dt, "updated_on":dt})
    return record_collection, admin_collection, import_collection, accounts_collection, mocker

def test_login_endpoint_without_session(app_db):
    # For now, setting mock_app to be global so that all the endpoints are already registered for subsequent tests
    # this is not reliable. The biggest issue is subsequent tests' 'user.routes.get_app_and_objects' doesn't get reloaded
    # and mock_app doesn't get registered with endpoints in their tests. 
    # global mock_app, mock_mongo_client, mocker
    mock_app, mock_mongo_client, mocker = app_db
    _, admin_collection, _, _, mocker = get_mocked_and_patched_collections(mocker)
    mock_time_keeper_dao = TimeKeeperDao(mock_mongo_client)
    fake_user = User(mongo_client=mock_mongo_client, time_keeper_dao=mock_time_keeper_dao)

    mocker.patch('src.create_app', return_value=(mock_app, mock_mongo_client))
    mocker.patch('user.routes.get_app_and_objects', return_value=(mock_app, mock_time_keeper_dao, fake_user))

    # Basic is unittest:123, and login successful
    rep = mock_app.test_client().get('/api/v1.0/user', headers={"Authorization": "Basic dW5pdHRlc3Q6MTIz"})
    assert '200 OK' == rep.status
    assert 'unittest' == rep.json['user_name']
    assert 0 == rep.json['used_minutes']
    assert 35 == rep.json['remaining_minutes']
    assert 35 == rep.json['topup_minutes']

    # login failure with error credential
    rep = mock_app.test_client().get('/api/v1.0/user', headers={"Authorization": "Basic test_not_exist:123"})
    assert '401 UNAUTHORIZED' == rep.status
    
    # test get_admin_stats get endpoint
    datetime_tmp = datetime.strptime("2021-11-25", '%Y-%m-%d')
    datetime_tmp_zero_minute = datetime_tmp.replace(hour=0,minute=0,second=0,microsecond=0)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_today', return_value=datetime_tmp)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_today_daytime', return_value=(datetime_tmp,datetime_tmp_zero_minute))

    datetime_tmp = datetime.strptime("2021-11-25", '%Y-%m-%d')
    dr_gt = [(datetime_tmp+timedelta(-i)).strftime('%Y-%m-%d') for i in range(13, -1, -1)]
    rep = mock_app.test_client().get('/api/v1.0/get_admin_stats', headers={"Authorization": "Basic dW5pdHRlc3Q6MTIz"})
    assert '200 OK' == rep.status
    assert rep.json['Pause'] == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    assert rep.json['Success'] == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
    assert rep.json['date_range'] == dr_gt
    assert rep.json['action_labels'] == ['Pause', 'Unpause', 'wifion']
    assert rep.json['attempt_labels'] == ['Success', 'Fail']

    # test get_time_stats get endpoint
    rep = mock_app.test_client().get('/api/v1.0/get_time_stats', headers={"Authorization": "Basic dW5pdHRlc3Q6MTIz"})
    assert '200 OK' == rep.status
    assert rep.json['date_range'] == dr_gt
    assert rep.json['added'] == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 35, 0]
    assert rep.json['used'] == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    assert rep.json['hours'] == ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
    assert rep.json['ampm'] == ['am', 'pm']
    assert rep.json['pm_hit_count'] == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    assert rep.json['am_hit_count'] == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]

    # test /api/v1.0/minutes get endpoint with incorrect param
    rep = mock_app.test_client().get(f'/api/v1.0/minutes?type=added&date=abc', headers={"Authorization": "Basic dW5pdHRlc3Q6MTIz"})
    assert '400 BAD REQUEST' == rep.status
    assert 'invalid parameter, correct type is ?type=[added|used]&date=[YYYY-MM-DD]' == rep.json['error']


    # test /api/v1.0/minutes get endpoint with incorrect param
    # "2021-11-24" has added time, "2021-11-25" doesn't have added time
    rep = mock_app.test_client().get(f'/api/v1.0/minutes?type=added&date=2021-11-24', headers={"Authorization": "Basic dW5pdHRlc3Q6MTIz"})
    assert '200 OK' == rep.status
    assert [35] == rep.json['added']
    rep = mock_app.test_client().get(f'/api/v1.0/minutes?type=added&date=2021-11-25', headers={"Authorization": "Basic dW5pdHRlc3Q6MTIz"})
    assert '200 OK' == rep.status
    assert [] == rep.json['added']

    # test /api/v1.0/minutes get endpoint with incorrect param
    # "2021-11-24" has used time, "2021-11-25" doesn't have used time
    rep = mock_app.test_client().get(f'/api/v1.0/minutes?type=used&date=2021-11-24', headers={"Authorization": "Basic dW5pdHRlc3Q6MTIz"})
    assert '200 OK' == rep.status
    assert [0] == rep.json['used']
    rep = mock_app.test_client().get(f'/api/v1.0/minutes?type=used&date=2021-11-25', headers={"Authorization": "Basic dW5pdHRlc3Q6MTIz"})
    assert '200 OK' == rep.status
    assert [] == rep.json['used']

    rep = mock_app.test_client().post(
        '/api/v1.0/minutes', 
        headers={"Authorization": "Basic dW5pdHRlc3Q6MTIz"}, 
        data=json.dumps({"minutes": 1000,"type": "added"})
    )
    assert '200 OK' == rep.status
    assert 1035 == rep.json['remaining_minutes']

    rep = mock_app.test_client().post(
        '/api/v1.0/minutes', 
        headers={"Authorization": "Basic dW5pdHRlc3Q6MTIz"}, 
        data=json.dumps({"minutes": 1000,"type": "used"})
    )
    assert '200 OK' == rep.status
    assert 35 == rep.json['remaining_minutes']


    # test POST /api/v1.0/admin_action endpoint
    action = []
    unittest_actions = admin_collection.find({"action":"Pause"})
    for ua in unittest_actions:
        action.append(ua)
    assert len(action) == 0
    rep = mock_app.test_client().post(
        '/api/v1.0/admin_action', 
        headers={"Authorization": "Basic dW5pdHRlc3Q6MTIz"}, 
        data=json.dumps({"action": "Pause","is_successful": True})
    ) 
    
    assert '200 OK' == rep.status
    unittest_actions = admin_collection.find({"action":"Pause"})
    for ua in unittest_actions:
        action.append(ua)
    assert 1 == len(action)
    assert action[0]['action'] == 'Pause'


from pytest_mock import mocker
from time_management.timekeeperdao import TimeKeeperDao
from datetime import datetime
from werkzeug.security import generate_password_hash

from user.user import User
import mongomock

mock_app = None
mock_mongo_client = None
mocker = None
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
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"unittest", "minutesAdded":[35]})
    admin_collection.insert_one({"datetime":datetime_tmp, "user":"unittest", "action":"Unpause", "is_success":True})
    import_collection.insert_one({"user":"unittest", "logline":"2022-02-14,topup,1"})
    dt = datetime.fromtimestamp(0)
    accounts_collection.insert_one({"name": "unittest","email": "test@test.com","password": generate_password_hash("123"), "created_on":dt, "updated_on":dt})
    return record_collection, admin_collection, import_collection, accounts_collection, mocker

def test_login_endpoint_without_session(app_db):
    # For now, setting mock_app to be global so that all the endpoints are already registered for subsequent tests
    # this is not reliable. The biggest issue is subsequent tests' 'user.routes.get_app_and_objects' doesn't get reloaded
    # and mock_app doesn't get registered with endpoints in their tests. 
    global mock_app, mock_mongo_client, mocker
    mock_app, mock_mongo_client, mocker = app_db
    _, _, _, _, mocker = get_mocked_and_patched_collections(mocker)
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
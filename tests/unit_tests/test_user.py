import mongomock
from time_management.timekeeperdao import TimeKeeperDao
from datetime import datetime
from user.user import User

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
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})
    admin_collection.insert_one({"datetime":datetime_tmp, "user":"test", "action":"Unpause", "is_success":True})
    import_collection.insert_one({"user":"test", "logline":"2022-02-14,topup,1"})
    return record_collection, admin_collection, import_collection, accounts_collection, mocker

def test_success_create_user_without_acc_coll(app_db):
    _, mock_mongo_client, mocker = app_db

    _, _, _, accounts_collection, mocker = get_mocked_and_patched_collections(mocker)

    mocker.patch('flask_pymongo.wrappers.Database.list_collection_names', return_value=["records", "admin", "imports"])

    acc = User(mongo_client=mock_mongo_client, time_keeper_dao=TimeKeeperDao(mongo_client=mock_mongo_client))
    acc = [c for c in accounts_collection.find({})]
    assert 1 == len(acc)

def test_acc_exist(app_db):
    _, mock_mongo_client, mocker = app_db

    _, _, _, accounts_collection, mocker = get_mocked_and_patched_collections(mocker)
    accounts_collection.insert_one({"name": "test_exist","email": "test@au4tech.com","password": "", "created_on":datetime.fromtimestamp(0), "updated_on":datetime.fromtimestamp(0)})

    acc = User(mongo_client=mock_mongo_client, time_keeper_dao=TimeKeeperDao(mongo_client=mock_mongo_client))
    assert True == acc.acc_name_exist("test_exist")
    assert False == acc.acc_name_exist("test_exist_no")

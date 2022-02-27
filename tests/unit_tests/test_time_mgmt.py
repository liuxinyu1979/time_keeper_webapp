from flask_pymongo import PyMongo
from time_management.timekeeperdao import TimeKeeperDao
import mongomock

import pytest
# https://pypi.org/project/pytest-mock/

# @pytest.mark.skip
def test_create_timekeeperdao_success_basic(app_db):
    _, mongo_client, mocker = app_db

    fake_db_exist = True
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.init_with_db', return_value=fake_db_exist)

    tkd = TimeKeeperDao(mongo_client=mongo_client)
    assert tkd.mongo == mongo_client
    assert tkd.db_exist == fake_db_exist

def test_successful_create_timekeeperdao_with_all_collections(app_db):
    app, mongo_client, mocker = app_db

    record_collection = mongomock.MongoClient().db.records
    record_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "minutesAdded":[35]})
    admin_collection = mongomock.MongoClient().db.admin
    admin_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "action":"Unpause", "is_success":"true"})
    import_collection = mongomock.MongoClient().db.imports
    import_collection.insert_one({"user":"test", "logline":"2022-02-14,topup,1"})


    mocker.patch('flask_pymongo.wrappers.MongoClient.server_info', side_effect={})
    mocker.patch('flask_pymongo.wrappers.Database.list_collection_names', return_value=["admin", "records", "imports"])
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_records_collection', return_value=record_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_imports_collection', return_value=import_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_admin_collection', return_value=admin_collection)

    tkd = TimeKeeperDao(mongo_client=mongo_client)

    assert tkd.db_exist == True
    assert tkd.users == {"test_no_name", "test"}
    assert tkd.remaining_minutes == {"test_no_name":0, "test":35}
    assert tkd.topup_minutes == {"test":35}
    assert tkd.used_minutes == {"test":0}

def test_fail_create_timekeeperdao_with_only_admin_collection(app_db):
    app, mongo_client, mocker = app_db
    admin_collection = mongomock.MongoClient().db.admin
    admin_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "action":"Unpause", "is_success":"true"})

    mocker.patch('flask_pymongo.wrappers.MongoClient.server_info', side_effect={})
    mocker.patch('flask_pymongo.wrappers.Database.list_collection_names', return_value=["admin"])
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_admin_collection', return_value=admin_collection)

    tkd = TimeKeeperDao(mongo_client=mongo_client)
    assert tkd.db_exist == False

def test_fail_create_timekeeperdao_with_only_imports_collection(app_db):
    app, mongo_client, mocker = app_db
    import_collection = mongomock.MongoClient().db.imports
    import_collection.insert_one({"user":"test", "logline":"2022-02-14,topup,1"})

    mocker.patch('flask_pymongo.wrappers.MongoClient.server_info', side_effect={})
    mocker.patch('flask_pymongo.wrappers.Database.list_collection_names', return_value=["imports"])
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_imports_collection', return_value=import_collection)

    tkd = TimeKeeperDao(mongo_client=mongo_client)
    assert tkd.db_exist == False


# test missing imports collection
def test_successful_create_timekeeperdao_when_missing_imports_collections(app_db):
    app, mongo_client, mocker = app_db

    record_collection = mongomock.MongoClient().db.records
    record_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "minutesAdded":[35]})
    admin_collection = mongomock.MongoClient().db.admin
    admin_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "action":"Unpause", "is_success":"true"})
    import_collection = mongomock.MongoClient().db.imports

    mocker.patch('flask_pymongo.wrappers.MongoClient.server_info', side_effect={})
    mocker.patch('flask_pymongo.wrappers.Database.list_collection_names', return_value=["admin", "records"])
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_records_collection', return_value=record_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_admin_collection', return_value=admin_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_imports_collection', return_value=import_collection)
    # imp_spy = mocker.spy('mongomock.MongoClient.db.imports', "insert_one")
    tkd = TimeKeeperDao(mongo_client=mongo_client)

    assert tkd.db_exist == True
    assert tkd.users == {"test_no_name", "test"}
    assert tkd.remaining_minutes == {"test_no_name":0, "test":35}
    assert tkd.topup_minutes == {"test":35}
    assert tkd.used_minutes == {"test":0}
    # assert imp_spy.call_count == 1
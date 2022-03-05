from flask_pymongo import PyMongo
from time_management.timekeeperdao import TimeKeeperDao
import mongomock
from datetime import datetime


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
    _, mongo_client, mocker = app_db

    record_collection = mongomock.MongoClient().db.records
    record_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "minutesAdded":[35]})
    admin_collection = mongomock.MongoClient().db.admin
    admin_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "action":"Unpause", "is_success":"true"})
    import_collection = mongomock.MongoClient().db.imports
    import_collection.insert_one({"user":"test", "logline":"2022-02-14,topup,1"})

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
    _, mongo_client, mocker = app_db
    admin_collection = mongomock.MongoClient().db.admin
    admin_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "action":"Unpause", "is_success":"true"})

    mocker.patch('flask_pymongo.wrappers.Database.list_collection_names', return_value=["admin"])
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_admin_collection', return_value=admin_collection)

    tkd = TimeKeeperDao(mongo_client=mongo_client)
    assert tkd.db_exist == False

def test_fail_create_timekeeperdao_with_only_imports_collection(app_db):
    _, mongo_client, mocker = app_db
    import_collection = mongomock.MongoClient().db.imports
    import_collection.insert_one({"user":"test", "logline":"2022-02-14,topup,1"})

    mocker.patch('flask_pymongo.wrappers.Database.list_collection_names', return_value=["imports"])
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_imports_collection', return_value=import_collection)

    tkd = TimeKeeperDao(mongo_client=mongo_client)
    assert tkd.db_exist == False

def test_successful_create_timekeeperdao_when_missing_imports_collections(app_db):
    _, mongo_client, mocker = app_db

    record_collection = mongomock.MongoClient().db.records
    record_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "minutesAdded":[35]})
    admin_collection = mongomock.MongoClient().db.admin
    admin_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "action":"Unpause", "is_success":"true"})
    import_collection = mongomock.MongoClient().db.imports

    mocker.patch('flask_pymongo.wrappers.Database.list_collection_names', return_value=["admin", "records"])
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_records_collection', return_value=record_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_admin_collection', return_value=admin_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_imports_collection', return_value=import_collection)
    imp_spy = mocker.spy(import_collection, "insert_one")
    tkd = TimeKeeperDao(mongo_client=mongo_client)

    assert tkd.db_exist == True
    assert tkd.users == {"test_no_name", "test"}
    assert tkd.remaining_minutes == {"test_no_name":0, "test":35}
    assert tkd.topup_minutes == {"test":35}
    assert tkd.used_minutes == {"test":0}
    assert imp_spy.call_count == 1

def test_successful_create_timekeeperdao_only_records_coll_and_only_used_minutes(app_db):
    _, mongo_client, mocker = app_db

    record_collection = mongomock.MongoClient().db.records
    record_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "minutesUsed":[5]})
    admin_collection = mongomock.MongoClient().db.admin
    import_collection = mongomock.MongoClient().db.imports
    imp_spy = mocker.spy(import_collection, "insert_one")
    admin_spy = mocker.spy(admin_collection, "insert_one")
    
    mocker.patch('flask_pymongo.wrappers.Database.list_collection_names', return_value=["records"])
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_records_collection', return_value=record_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_imports_collection', return_value=import_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_admin_collection', return_value=admin_collection)

    tkd = TimeKeeperDao(mongo_client=mongo_client)

    assert tkd.db_exist == True
    assert tkd.users == {"test_no_name", "test"}
    assert tkd.remaining_minutes == {"test_no_name":0, "test":-5}
    assert tkd.topup_minutes == {"test":0}
    assert tkd.used_minutes == {"test":5}
    assert imp_spy.call_count == 1
    assert admin_spy.call_count == 1

def test_successful_export_user_time_to_csv(app_db):
    _, mongo_client, mocker = app_db
    record_collection = mongomock.MongoClient().db.records
    datetime_tmp = datetime.strptime("2021-11-24", '%Y-%m-%d')
    record_collection.insert_one({"datetime":datetime_tmp, "user":"test", "minutesAdded":[35], "minutesUsed":[30]})
    admin_collection = mongomock.MongoClient().db.admin
    admin_collection.insert_one({"datetime":datetime_tmp, "user":"test", "action":"Unpause", "is_success":"true"})
    import_collection = mongomock.MongoClient().db.imports
    import_collection.insert_one({"user":"test", "logline":"2022-02-14,topup,1"})

    mocker.patch('flask_pymongo.wrappers.Database.list_collection_names', return_value=["admin", "records", "imports"])
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_records_collection', return_value=record_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_imports_collection', return_value=import_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_admin_collection', return_value=admin_collection)

    tkd = TimeKeeperDao(mongo_client=mongo_client)
    assert tkd.db_exist == True
    assert tkd.users == {"test_no_name", "test"}
    assert tkd.remaining_minutes == {"test_no_name":0, "test":5}
    assert tkd.topup_minutes == {"test":35}
    assert tkd.used_minutes == {"test":30}

    content = tkd.export_time_to_csv("test")
    assert 'date time,action,minute\n2021-11-24,topup,35\n2021-11-24,used,30' == content

def test_correct_records_coll_doc_count(app_db):
    _, mongo_client, mocker = app_db
    record_collection = mongomock.MongoClient().db.records
    record_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35], "minutesUsed":[30]})
    admin_collection = mongomock.MongoClient().db.admin
    import_collection = mongomock.MongoClient().db.imports

    mocker.patch('flask_pymongo.wrappers.Database.list_collection_names', return_value=["records"])
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_records_collection', return_value=record_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_imports_collection', return_value=import_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_admin_collection', return_value=admin_collection)

    tkd = TimeKeeperDao(mongo_client=mongo_client)
    assert 1 == tkd.document_count("test")
    assert 0 == tkd.document_count("test_no_name")


def test_correct_pagination_records_coll_(app_db):
    _, mongo_client, mocker = app_db
    record_collection = mongomock.MongoClient().db.records
    # 6 documents
    for i in range(1, 7):
        date_str = str(i)
        record_collection.insert_one({"datetime":f"2021-11-{i}T00:00:00.000+00:0", "user":"test", "minutesAdded":[i]})
    admin_collection = mongomock.MongoClient().db.admin
    import_collection = mongomock.MongoClient().db.imports

    mocker.patch('flask_pymongo.wrappers.Database.list_collection_names', return_value=["records", "admin", "imports"])
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_records_collection', return_value=record_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_imports_collection', return_value=import_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_admin_collection', return_value=admin_collection)

    tkd = TimeKeeperDao(mongo_client=mongo_client)
    # above inserted 6 documents, enough for 3 pages
    page_limit = 2
    for i in range(3):
        page_num = i
        records = tkd.find_documents_by_page("test", page_num=page_num+1, per_page_limit=page_limit)
        # todo: find how to count number of records given cursor
        c = 0
        for r in records:
            c+=1
        assert c == 2
        assert records[0]['minutesAdded'] == [i*2+1]
        assert records[1]['minutesAdded'] == [i*2+2]


def test_failed_due_to_pagination_input_records_coll_(app_db):
    _, mongo_client, mocker = app_db
    record_collection = mongomock.MongoClient().db.records
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})
    admin_collection = mongomock.MongoClient().db.admin
    import_collection = mongomock.MongoClient().db.imports

    mocker.patch('flask_pymongo.wrappers.Database.list_collection_names', return_value=["records", "admin", "imports"])
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_records_collection', return_value=record_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_imports_collection', return_value=import_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_admin_collection', return_value=admin_collection)

    tkd = TimeKeeperDao(mongo_client=mongo_client)
    records = tkd.find_documents_by_page("test", page_num=0, per_page_limit=2)
    assert None == records
    records = tkd.find_documents_by_page("test", page_num=-1, per_page_limit=2)
    assert None == records
    records = tkd.find_documents_by_page("test", page_num=1, per_page_limit=0)
    assert None == records
    records = tkd.find_documents_by_page("test", page_num=1, per_page_limit=-1)
    assert None == records



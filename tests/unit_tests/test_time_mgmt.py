from flask_pymongo import PyMongo
from time_management.timekeeperdao import TimeKeeperDao, AdminAction, TimeAction
import mongomock
from datetime import datetime, timedelta


import pytest
# https://pypi.org/project/pytest-mock/


def get_mocked_collections():
    record_collection = mongomock.MongoClient().db.records
    admin_collection = mongomock.MongoClient().db.admin
    import_collection = mongomock.MongoClient().db.imports

    return record_collection, admin_collection, import_collection

def get_mocked_and_patched_collections(mocker):
    record_collection, admin_collection, import_collection = get_mocked_collections()
    mocker.patch('flask_pymongo.wrappers.Database.list_collection_names', return_value=["records", "admin", "imports"])
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_records_collection', return_value=record_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_imports_collection', return_value=import_collection)
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.get_admin_collection', return_value=admin_collection)
    return record_collection, admin_collection, import_collection, mocker

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
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)

    record_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "minutesAdded":[35]})
    admin_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "action":"Unpause", "is_success":"true"})
    import_collection.insert_one({"user":"test", "logline":"2022-02-14,topup,1"})

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
    record_collection, admin_collection, import_collection = get_mocked_collections()
    record_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "minutesAdded":[35]})
    admin_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "action":"Unpause", "is_success":"true"})

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
    record_collection, admin_collection, import_collection = get_mocked_collections()
    record_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:00", "user":"test", "minutesUsed":[5]})
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
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    
    datetime_tmp = datetime.strptime("2021-11-24", '%Y-%m-%d')
    record_collection.insert_one({"datetime":datetime_tmp, "user":"test", "minutesAdded":[35], "minutesUsed":[30]})
    admin_collection.insert_one({"datetime":datetime_tmp, "user":"test", "action":"Unpause", "is_success":"true"})
    import_collection.insert_one({"user":"test", "logline":"2022-02-14,topup,1"})

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
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35], "minutesUsed":[30]})

    tkd = TimeKeeperDao(mongo_client=mongo_client)
    assert 1 == tkd.document_count("test")
    assert 0 == tkd.document_count("test_no_name")


def test_correct_pagination_records_coll(app_db):
    _, mongo_client, mocker = app_db

    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    # 6 documents
    for i in range(1, 7):
        date_str = str(i)
        record_collection.insert_one({"datetime":f"2021-11-{i}T00:00:00.000+00:0", "user":"test", "minutesAdded":[i]})

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

def test_fail_due_to_pagination_input_records_coll(app_db):
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})

    tkd = TimeKeeperDao(mongo_client=mongo_client)
    records = tkd.find_documents_by_page("test", page_num=0, per_page_limit=2)
    assert None == records
    records = tkd.find_documents_by_page("test", page_num=-1, per_page_limit=2)
    assert None == records
    records = tkd.find_documents_by_page("test", page_num=1, per_page_limit=0)
    assert None == records
    records = tkd.find_documents_by_page("test", page_num=1, per_page_limit=-1)
    assert None == records

def test_success_get_user_time_info(app_db):
    user_name = "test"
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})
    tkd = TimeKeeperDao(mongo_client=mongo_client)
    remain_min, topup_min, used_min = tkd.get_user_time_info(user_name)
    assert remain_min == 35 and topup_min == 35 and used_min == 0

    min_topup = tkd.minutes_toppedup(user_name)
    min_used = tkd.minutes_used(user_name)
    min_remain = tkd.minutes_left(user_name)
    assert min_remain == 35 and min_topup == 35 and min_used == 0

def test_fail_get_user_time_info(app_db):
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})
    tkd = TimeKeeperDao(mongo_client=mongo_client)
    remain_min, topup_min, used_min = tkd.get_user_time_info("test_acc_nonexist")
    assert remain_min == -1 and topup_min == -1 and used_min == -1

def test_success_record_admin_action(app_db):
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})
    tkd = TimeKeeperDao(mongo_client=mongo_client)
    for aa in AdminAction:
        ret, err = tkd.record_admin_action(aa.name, True, "test")
        admin_action = tkd.admin_action_get_one()
        assert ret == True and err == "" and admin_action['is_success'] == True and admin_action['action'] == aa.name
        admin_collection.find_one_and_delete({'_id':admin_action['_id']})

def test_fail_record_admin_action(app_db):
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})
    tkd = TimeKeeperDao(mongo_client=mongo_client)
    ret, err = tkd.record_admin_action("invalid_admin_action", True, "test")
    assert ret == False and err == "Unrecognized admin action"

def test_success_record_minutes_added(app_db):
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})
    tkd = TimeKeeperDao(mongo_client=mongo_client)
    ret, err = tkd.record_minutes_added(5, "test")
    assert ret["remaining_minutes"] == 40 and err == ""

def test_fail_record_minutes_added(app_db):
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})
    tkd = TimeKeeperDao(mongo_client=mongo_client)
    ret, err = tkd.record_minutes_added(-1, "test")
    assert ret == {} and len(err) > 0

    ret, err = tkd.record_minutes_added(5, "test_acc_nonexist")
    assert ret == {} and len(err) > 0

def test_success_record_minutes_used(app_db):
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})
    tkd = TimeKeeperDao(mongo_client=mongo_client)
    ret, err = tkd.record_minutes_used(5, "test")
    assert ret["remaining_minutes"] == 30 and err == ""

def test_fail_record_minutes_used(app_db):
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})
    tkd = TimeKeeperDao(mongo_client=mongo_client)
    ret, err = tkd.record_minutes_added(-1, "test")
    assert ret == {} and len(err) > 0

    ret, err = tkd.record_minutes_added(5, "test_acc_nonexist")
    assert ret == {} and len(err) > 0

def test_success_get_minutes_in_db(app_db):
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})
    tkd = TimeKeeperDao(mongo_client=mongo_client)

    records, err = tkd.get_minutes_in_db("test", "1970-11-24T00:00:00.000+00:0")
    assert err == "" and records == None

    records, err = tkd.get_minutes_in_db("test", "2021-11-24T00:00:00.000+00:0")
    assert err == "" and records['minutesAdded'] == [35]

def test_fail_get_minutes_in_db(app_db):
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})
    tkd = TimeKeeperDao(mongo_client=mongo_client)
    records, err = tkd.get_minutes_in_db("test_acc_nonexist", "1970-11-24T00:00:00.000+00:0")
    assert records == {} and len(err) > 0

def test_success_record_time_and_logline(app_db):
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})
    tkd = TimeKeeperDao(mongo_client=mongo_client)
    time_in_minute = 10
    record, err = tkd.record_time_and_logline(TimeAction.topup.name, time_in_minute, "test")
    assert record["remaining_minutes"] == 45 and err == ""
    record, err = tkd.record_time_and_logline(TimeAction.used.name, time_in_minute, "test")
    assert record["remaining_minutes"] == 35 and err == ""

    # If we run this test in midnight, then there is a slight chance the dt recorded in record_time_and_logline method 
    # is the day x and dt here is the next day
    dt = datetime.today().strftime('%Y-%m-%d')
    import_collection_gt = [f"{dt},{TimeAction.topup.name},{time_in_minute}", f"{dt},{TimeAction.used.name},{time_in_minute}"]
    cursor = import_collection.find({})
    vals = []
    for c in cursor:
        vals.append(c["logline"])
    assert import_collection_gt == vals

def test_fail_record_time_and_logline(app_db):
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})

    tkd = TimeKeeperDao(mongo_client=mongo_client)
    ret, err = tkd.record_time_and_logline(TimeAction.topup.name, -1, "test")
    assert ret == {} and len(err) > 0
    ret, err = tkd.record_time_and_logline(TimeAction.topup.name, 5, "test_acc_nonexist")
    assert ret == {} and len(err) > 0
    ret, err = tkd.record_time_and_logline("invalid_action", 5, "test")
    assert ret == {} and len(err) > 0

def test_success_retrieve_admin_stat_all_14_days(app_db):
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})

    # fake 14 days of admin actions
    current_date = datetime.today() 
    dr_gt = [(current_date+timedelta(-i)).strftime('%Y-%m-%d') for i in range(13, -1, -1)]
    is_success_hit_count_gt = [[0 for i in range(len(dr_gt))], [0 for i in range(len(dr_gt))]]
    actions_hit_count_gt = [[0 for i in range(len(dr_gt))], [0 for i in range(len(dr_gt))], [0 for i in range(len(dr_gt))]]
    for i in range(13, -1, -1):
        datetime_tmp =current_date+timedelta(-i)
        admin_collection.insert_one({"datetime":datetime_tmp, "user":"test", "action":"Unpause", "is_success":True})
        actions_hit_count_gt[1][i] += 1 
        is_success_hit_count_gt[0][i] += 1 

    tkd = TimeKeeperDao(mongo_client=mongo_client)
    is_success, dr, is_success_hit_count, actions, actions_hit_count = tkd.retrieve_admin_stat("test")
    assert is_success == ['Success', 'Fail']
    assert actions == [AdminAction.Pause.name, AdminAction.Unpause.name, AdminAction.wifion.name]
    assert dr_gt == dr
    # Due to the timing issue, retrieve_admin_stat's 'datetime': {'$gt': date_range[0], '$lt': date_range[1]} filter
    # may filter out the first and/or last
    assert actions_hit_count_gt[0] == actions_hit_count[0]
    assert actions_hit_count_gt[1][1:-1] == actions_hit_count[1][1:-1]
    assert actions_hit_count_gt[2] == actions_hit_count[2]

    assert is_success_hit_count_gt[0][1:-1] == is_success_hit_count[0][1:-1]
    assert is_success_hit_count_gt[1] == is_success_hit_count[1]

def test_success_retrieve_admin_stat_14_days_no_data(app_db):
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    record_collection.insert_one({"datetime":f"2021-11-24T00:00:00.000+00:0", "user":"test", "minutesAdded":[35]})

    tkd = TimeKeeperDao(mongo_client=mongo_client)
    is_success, dr, is_success_hit_count, actions, actions_hit_count = tkd.retrieve_admin_stat("test")
    current_date = datetime.today() 
    dr_gt = [(current_date+timedelta(-i)).strftime('%Y-%m-%d') for i in range(13, -1, -1)]
    is_success_hit_count_gt = [[0 for i in range(len(dr_gt))], [0 for i in range(len(dr_gt))]]
    actions_hit_count_gt = [[0 for i in range(len(dr_gt))], [0 for i in range(len(dr_gt))], [0 for i in range(len(dr_gt))]]

    assert is_success == ['Success', 'Fail']
    assert actions == [AdminAction.Pause.name, AdminAction.Unpause.name, AdminAction.wifion.name]
    assert dr_gt == dr
    assert is_success_hit_count_gt == is_success_hit_count
    assert actions_hit_count_gt == actions_hit_count
 
def test_success_retrieve_time_stat_all_14_days(app_db):
    _, mongo_client, mocker = app_db
    record_collection, admin_collection, import_collection, mocker = get_mocked_and_patched_collections(mocker)
    current_date = datetime.today().replace(hour=0,minute=0,second=0,microsecond=0)
    dr_gt = [(current_date+timedelta(-i)).strftime('%Y-%m-%d') for i in range(13, -1, -1)]

    day_count = 14
    min_added = 5
    min_used = 1
    # fake minutesUsedTimeStamp for hr 1 to hr 13
    for i in range(day_count-1, -1, -1):
        timestamp_part = {"hr":i, "minute": 0, "second": 0}
        datetime_tmp =(current_date+timedelta(-i)).replace(hour=0,minute=0,second=0,microsecond=0)
        record_collection.insert_one({"datetime":datetime_tmp, "user":"test", "minutesAdded":[min_added], "minutesUsed": [min_used], 'minutesUsedTimeStamp':timestamp_part})
    
    tkd = TimeKeeperDao(mongo_client=mongo_client)
    date_range, used, added, ampm, hrs, hit_count_vals = tkd.retrieve_for_time_stat(0, 1, "test")
    assert ampm == ["am", "pm"]
    assert hrs == ["1","2","3","4","5","6","7","8","9","10","11","12"]
    assert date_range == dr_gt
    assert added == [min_added]*day_count
    assert used == [min_used]*day_count
    assert hit_count_vals[0] == [1]*12
    assert hit_count_vals[1] == [1]+[0]*11

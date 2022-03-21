import flask_pymongo
# from flask_pymongo import PyMongo
from datetime import datetime, timedelta

from enum import Enum

AdminAction = Enum('AdminAction', 'Pause Unpause wifion')
TimeAction = Enum('TimeAction', 'used topup')

class TimeKeeperDao:
    def __init__(self, mongo_client):
        self.test_acc = "test_no_name"
        self.users = {self.test_acc}
        self.remaining_minutes = {}
        self.topup_minutes = {}
        self.used_minutes = {}
        # todo: deal with the user based import
        self.input_lines = set()

        self.mongo = mongo_client

        self.time_db_tracker_records = None
        self.time_db_tracker_imports = None
        self.time_db_tracker_admin = None

        self.TIME_FILE_HEADER = "date time,action,minute"

        self.WEEKEND_REWARD_CONS_MINUTES = 35 # a one-off 35 minutes reward on Friday/Saturday/Sunday
        self.INIT_RECORD_TABLE_PAYLOAD = {"user":self.test_acc, "datetime":datetime.fromtimestamp(0), 'minutesUsed':[], 'minutesAdded':[self.WEEKEND_REWARD_CONS_MINUTES]}
        self.INIT_ADMIN_TABLE_PAYLOAD = {"user":self.test_acc, "datetime":datetime.fromtimestamp(0), 'action':AdminAction.Unpause.name, 'is_success':False}
        self.INIT_IMPORTS_TABLE_PAYLOAD = {"user":self.test_acc, "logline":f"1970-01-01,topup,{self.WEEKEND_REWARD_CONS_MINUTES}"}

        self.db_exist = self.init_with_db()
    
    def get_action_label(self, input_action):
        if input_action == TimeAction.used.name:
            return "Drawdown"
        return "Topup"

    def init_with_db(self):
        self.time_db_tracker_records = self.get_records_collection()
        self.time_db_tracker_imports = self.get_imports_collection()
        self.time_db_tracker_admin = self.get_admin_collection()

        collection_names= set(self.mongo.db.list_collection_names())

        if "records" not in collection_names and ("admin" in collection_names or "imports" in collection_names):
            return False

        record_cnt = 0
        for doc in self.time_db_tracker_records.find():
            record_cnt += 1
            user_name = self.test_acc
            if "user" in doc:
                user_name = doc['user']
            if user_name not in self.users:
                self.users.add(user_name)
                self.topup_minutes[user_name] = 0
                self.used_minutes[user_name] = 0
                self.remaining_minutes[user_name] = 0

            if 'minutesUsed' in doc:
                if user_name in self.used_minutes:
                    self.used_minutes[user_name] += sum(doc['minutesUsed'])
                else:
                    self.used_minutes[user_name] = sum(doc['minutesUsed'])

            if 'minutesAdded' in doc:
                if user_name in self.topup_minutes:
                    self.topup_minutes[user_name] += sum(doc['minutesAdded'])
                else:
                    self.topup_minutes[user_name] = sum(doc['minutesAdded'])

        # if the table doesn't exist, initialize it with some number of minutes
        if record_cnt == 0:
            self.time_db_tracker_records.insert_one(self.INIT_RECORD_TABLE_PAYLOAD)
            self.time_db_tracker_admin.insert_one(self.INIT_ADMIN_TABLE_PAYLOAD)
            self.time_db_tracker_imports.insert_one(self.INIT_IMPORTS_TABLE_PAYLOAD)
            self.topup_minutes[self.test_acc]  = self.WEEKEND_REWARD_CONS_MINUTES

            self.time_db_tracker_records.create_index([("datetime", flask_pymongo.DESCENDING)], unique=True, name="datetimeIdx")
            self.time_db_tracker_admin.create_index([("datetime", flask_pymongo.DESCENDING)], unique=True, name="datetimeIdx")

        # add collection on the fly if database and some collections already exist
        if "admin" not in collection_names:
            self.time_db_tracker_admin.insert_one(self.INIT_ADMIN_TABLE_PAYLOAD)
            self.time_db_tracker_admin.create_index([("datetime", flask_pymongo.DESCENDING)], unique=True, name="datetimeIdx")
        if "imports" not in collection_names:
            self.time_db_tracker_imports.insert_one(self.INIT_IMPORTS_TABLE_PAYLOAD)
        
        for u_name in self.users:
            topup_minutes = 0
            if u_name in self.topup_minutes:
                topup_minutes = self.topup_minutes[u_name]

            used_minutes = 0
            if u_name in self.used_minutes:
                used_minutes = self.used_minutes[u_name]

            self.remaining_minutes[u_name] = topup_minutes - used_minutes

        return True


    def export_time_to_csv(self, user):
        content = self.TIME_FILE_HEADER
        records = self.time_db_tracker_records.find({'user':user})
        for doc in records:
            dt = doc['datetime'].strftime('%Y-%m-%d')
            if 'minutesAdded' in doc:
                content += f"\n{dt},topup,{sum(doc['minutesAdded'])}"
            if 'minutesUsed' in doc:
                content += f"\n{dt},used,{sum(doc['minutesUsed'])}"

        return content

    def document_count(self, user):
        return self.time_db_tracker_records.count_documents({'user':user})

    # page_num starts from 1, not 0
    def find_documents_by_page(self, user, page_num, per_page_limit):
        if user not in self.users or page_num <= 0  or per_page_limit <= 0:
            return None

        # find all the records from a user sorted ascending
        # skip to the right page, eg: if page_num is 1, then we start from document 1
        # if page_num is 2 and per_page_limit is 10, then we start from 10
        records = self.time_db_tracker_records.find({'user':user}).skip((page_num-1)*per_page_limit).limit(per_page_limit)
        return records

    def get_user_time_info(self, user):
        if user not in self.users:
            return -1, -1, -1
        return self.remaining_minutes[user], self.topup_minutes[user], self.used_minutes[user]

    def minutes_toppedup(self, user):
        return self.topup_minutes[user]
    def minutes_used(self, user):
        return self.used_minutes[user]

    def minutes_left(self, user):
        return self.remaining_minutes[user]

    def get_records_collection(self):
        return self.mongo.db.records

    def get_imports_collection(self):
        return self.mongo.db.imports
    
    def get_admin_collection(self):
        return self.mongo.db.admin

    # this is for testing only
    def admin_action_get_one(self):
        v = self.time_db_tracker_admin.find_one()
        return v

    def record_admin_action(self, admin_action, is_successful, user):
        if admin_action not in set([v.name for v in AdminAction]):
            return False, "Unrecognized admin action"
        self.time_db_tracker_admin.insert_one({'user':user, 'datetime':datetime.today(), 'action':admin_action, 'is_success':is_successful})
        return True, ""

    def get_today_daytime(self):
        today_time = datetime.today()
        today_time_zero_minute = today_time.replace(hour=0,minute=0,second=0,microsecond=0)
        return today_time, today_time_zero_minute

    def record_minutes_added(self, number_of_minutes, user):
        if number_of_minutes < 0 or user not in self.users:
            return {}, "Please check number of minutes {number_of_minutes} and user {user} are valid"
        _, today_time_zero_time = self.get_today_daytime()
        self.time_db_tracker_records.update_one({'user':user,'datetime':today_time_zero_time}, {'$push': {'minutesAdded':number_of_minutes}}, upsert=True)
        self.topup_minutes[user] += number_of_minutes
        self.remaining_minutes[user] = self.topup_minutes[user] - self.used_minutes[user]
        return {"remaining_minutes":self.remaining_minutes[user]}, ""

    def record_minutes_used(self, number_of_minutes, user):
        if number_of_minutes < 0 or user not in self.users:
            return {}, "Please check number of minutes {number_of_minutes} and user {user} are valid"
        
        today_time, tt = self.get_today_daytime()

        # today_time = datetime.today()
        # tt = today_time.replace(hour=0,minute=0,second=0,microsecond=0)
        timestamp_part = {"hr":today_time.hour, "minute": today_time.minute, "second": today_time.second}
        self.time_db_tracker_records.update_one({'user':user,'datetime':tt}, {'$push': {'minutesUsed':number_of_minutes}}, upsert=True)
        self.time_db_tracker_records.update_one({'user':user,'datetime':tt}, {'$push': {'minutesUsedTimeStamp':timestamp_part}}, upsert=True)
        
        self.used_minutes[user] += number_of_minutes
        self.remaining_minutes[user] = self.topup_minutes[user] - self.used_minutes[user]
        return {"remaining_minutes":self.remaining_minutes[user]}, ""

    def get_minutes_in_db(self, user, queried_date_time):
        if user not in self.users:
            return {}, "user {user} is not valid"
        rec = self.time_db_tracker_records.find_one({'user':user, 'datetime':queried_date_time})
        return rec, ""

    # this method is called from specify_time, meaning users enter add/used time instead of upload by file. 
    # We must record these manual input as if they are loglines from file upload. If we don't, and a user 
    # reupload a previously exported time file, we may double count some entries. Remeber, an exported time file
    # exports all the entries from "records" collection, not the "imports" collection
    def record_time_and_logline(self, input_action, input_minutes, user):
        if input_minutes < 0 or user not in self.users or (input_action != TimeAction.topup.name and input_action != TimeAction.used.name):
            return {}, "Please check number of minutes {number_of_minutes} and user {user} are valid"
        
        dt = datetime.today().strftime('%Y-%m-%d')
        logline = f"{dt},{input_action},{input_minutes}"

        if input_action == TimeAction.topup.name:
            self.record_minutes_added(input_minutes, user)
        elif input_action == TimeAction.used.name:
            self.record_minutes_used(input_minutes, user)

        self.time_db_tracker_imports.insert_one({'user':user,'logline': logline})
        return {"remaining_minutes":self.remaining_minutes[user]}, ""
    
    def get_today(self):
        return datetime.today() 

    # retrieve admin stats for the last 14 days
    def retrieve_admin_stat(self, user_name):
        is_success = ['Success', 'Fail']
        actions = [AdminAction.Pause.name, AdminAction.Unpause.name, AdminAction.wifion.name]
        current_date = self.get_today()
        dr = [(current_date+timedelta(-i)).strftime('%Y-%m-%d') for i in range(13, -1, -1)]
        lookup = {}
        for i in range(len(dr)):
            lookup[dr[i]] = i
        # hit_count[0] stores success count, hit_count[1] stores failure count
        is_success_hit_count = [[0 for i in range(len(dr))], [0 for i in range(len(dr))]]
        # actions[0] is pause, [1] is unpause, [2] is wifi
        actions_hit_count = [[0 for i in range(len(dr))], [0 for i in range(len(dr))], [0 for i in range(len(dr))]]
        date_range = (current_date+timedelta(-14), current_date)

        pl = [
            {
                '$match': {
                    "user":{'$eq': user_name},
                    'datetime': {
                        '$gt': date_range[0], 
                        '$lt': date_range[1]
                    }
                }
            }, {
                '$group': {
                    '_id': {
                        'date': {
                            '$dateToString': {
                                'date': '$datetime', 
                                'format': '%Y-%m-%d'
                            }
                        }, 
                        'action': '$action', 
                        'is_success': '$is_success'
                    }, 
                    'count': {
                        '$sum': 1
                    }
                }
            }, {
                '$sort': {
                    '_id.date': 1
                }
            }
        ]

        for doc in self.time_db_tracker_admin.aggregate(pipeline=pl):
            if doc['_id']['date'] not in lookup:
                continue
            idx = lookup[doc['_id']['date']]

            if doc['_id']['action'] == AdminAction.Pause.name:
                actions_hit_count[0][idx] += doc['count']
            elif doc['_id']['action'] == AdminAction.Unpause.name:
                actions_hit_count[1][idx] += doc['count']
            else:
                actions_hit_count[2][idx] += doc['count']

            if doc['_id']['is_success'] == True:
                is_success_hit_count[0][idx] += doc['count']
            else:
                is_success_hit_count[1][idx] += doc['count']                

        return is_success, dr, is_success_hit_count, actions, actions_hit_count

    # retrieve time stats for the last 14 days
    def retrieve_for_time_stat(self, start, end, user_name):

        # parallel array
        # date_range->['2021-x-y', '2021-x-y', '2021-x-y']
        # used->[0, 0, 0]
        # added->[0,0,0]
        current_date = self.get_today()
        num_of_days = 14
        date_range = [(current_date+timedelta(days=-i)).strftime('%Y-%m-%d') for i in range(0, num_of_days)]
        lookup = {}
        for i in range(len(date_range)):
            lookup[date_range[i]] = i

        used = [0 for i in range(0, num_of_days)]
        added = [0 for i in range(0, num_of_days)]


        ampm = ["am", "pm"]
        am_hrs = 12
        # hour 1.. 12
        hrs = [str(i+1) for i in range(am_hrs)]
        # am is hit_count[0], hit_count[1]
        hit_count_vals = [[0 for i in range(am_hrs)], [0 for i in range(am_hrs)]]

        hitcount_pl = [
            {
                '$match': {
                    "user":{'$eq': user_name},
                    'datetime':{'$lte':datetime.strptime(date_range[0], '%Y-%m-%d'),'$gte':datetime.strptime(date_range[-1], '%Y-%m-%d')}
                }
            }, {
                '$unwind': {
                    'path': '$minutesUsedTimeStamp', 
                    'preserveNullAndEmptyArrays': False
                }
            }, {
                '$group': {
                    '_id': '$minutesUsedTimeStamp.hr', 
                    'count': {
                        '$sum': 1
                    }
                }
            }
        ]
        for doc in self.time_db_tracker_records.aggregate(pipeline=hitcount_pl):
            time_stamp_hr = doc['_id']
            ampm_idx = 0
            if doc['_id'] > 12:
                time_stamp_hr -= 12
                ampm_idx = 1
            hit_count_vals[ampm_idx][time_stamp_hr-1] = doc['count']
            

        used_added_minutes_pl = [
            {
                '$match': {
                    "user":{'$eq': user_name},
                    'datetime': {
                        '$lte': datetime.strptime(date_range[0], '%Y-%m-%d'), 
                        '$gte': datetime.strptime(date_range[-1], '%Y-%m-%d')
                    }
                }
            }, {
                '$project': {
                    'date': {
                        '$dateToString': {
                            'date': '$datetime', 
                            'format': '%Y-%m-%d'
                        }
                    }, 
                    'minutesUsedSum': {
                        '$sum': '$minutesUsed'
                    }, 
                    'minutesAddedSum': {
                        '$sum': '$minutesAdded'
                    }
                }
            }
        ]
        for doc in self.time_db_tracker_records.aggregate(pipeline=used_added_minutes_pl):
            loc = lookup[doc['date']]
            used[loc] = doc['minutesUsedSum']
            added[loc] = doc['minutesAddedSum']

        return date_range[::-1], used[::-1], added[::-1], ampm, hrs, hit_count_vals
 
    '''
    unit tested above
    '''
    # This method is typically called during user signup, as a one-off bonus
    # This method ignores negative inputs
    def init_time_vals_for_user(self, user, used_minutes, topup_minutes):
        # since it's init, we allow minutes to be 0. 
        if user in self.users:
            return
        self.users.add(user)
        self.topup_minutes[user] = 0
        self.used_minutes[user] = 0

        if topup_minutes > 0:
            self.record_minutes_added(topup_minutes,user)
        if used_minutes > 0:
            self.record_minutes_used(used_minutes,user)

    
    # imports time added and used to databases. 
    # The time added and used won't be recorded for the days did the topup. They will be recorded towards the day of import
    # this is because kids often save up a bunch of topup and used records, and when we upload time, we want to see them on the 
    # graphs right away, so we record the time towards date of upload, which is today
    def update_db_by_import(self, time_keeper_file, user):
        if user not in self.users:
            # TODO: check when does this happen, doesn't seem to be possible because a person needs to sign in before upload 
            # time records by file. 
            self.init_time_vals_for_user(user, 0, 35)

        # The file format is 
        # date time,action,minute
        # 2022-01-17,topup,999
        with open(time_keeper_file, "r") as in_file:
            # first line is to remove the header
            line = in_file.readline()
            if line.strip() != self.TIME_FILE_HEADER:
                return False
            line = in_file.readline()
            while line != None and line != '' and line != '\n':

                log = line.strip().replace(' ','').split(',')
                if len(log) != 3:
                    return False
                log_line = ",".join(log)
                # if the logline already exists in db, ignore it. 
                if self.time_db_tracker_imports.find_one({'user':user, 'logline': log_line}) == None:
                    self.time_db_tracker_imports.insert_one({'user':user,'logline': log_line})
                    v = int(log[2])
                    if log[1] == TimeAction.topup.name:
                        self.record_minutes_added(v, user)
                    elif log[1] == TimeAction.used.name:
                        self.record_minutes_used(v, user)

                line = in_file.readline()
        
        return True


import flask_pymongo
from flask_pymongo import PyMongo
from datetime import datetime, timedelta

from enum import Enum

AdminAction = Enum('AdminAction', 'Pause Unpause wifion')

class TimeKeeperDao:
    def __init__(self, app):
        self.test_acc = "test"
        self.users = {self.test_acc}
        self.remaining_minutes = {}
        self.topup_minutes = {}
        self.used_minutes = {}
        # todo: deal with the user based import
        self.input_lines = set()

        self.time_keeper_db_name = "testtimedb"

        self.mongo = PyMongo(app)
        self.time_db_tracker_records = None
        self.time_db_tracker_imports = None
        self.time_db_tracker_admin = None

        self.WEEKEND_REWARD_CONS_MINUTES = 35 # a one-off 35 minutes reward on Friday/Saturday/Sunday
        self.INIT_RECORD_TABLE_PAYLOAD = {"user":self.test_acc, "datetime":datetime.fromtimestamp(0), 'minutesUsed':[], 'minutesAdded':[self.WEEKEND_REWARD_CONS_MINUTES]}
        self.INIT_ADMIN_TABLE_PAYLOAD = {"user":self.test_acc, "datetime":datetime.fromtimestamp(0), 'action':AdminAction.Unpause.name, 'is_success':False}
        self.INIT_IMPORTS_TABLE_PAYLOAD = {"user":self.test_acc, "logline":f"1970-01-01,topup,{self.WEEKEND_REWARD_CONS_MINUTES}"}

        self.db_exist = self.init_with_db()




    def topup_minutes_in_db(self, number_of_minutes, user):
        if number_of_minutes < 0 or user not in self.users:
            return "Please check number of minutes {number_of_minutes} and user {user} are valid", False

        self.time_db_tracker_records.update_one({'user':user,'datetime':datetime.today().replace(hour=0,minute=0,second=0,microsecond=0)}, {'$push': {'minutesAdded':number_of_minutes}}, upsert=True)
        self.topup_minutes[user] += number_of_minutes
        self.remaining_minutes[user] = self.topup_minutes[user] - self.used_minutes[user]
        return "", True



    def admin_action_get_one(self):
        v = self.time_db_tracker_admin.find_one()
        return v

    
    def init_with_db(self):

        try:
            cx = self.mongo.cx.server_info()
            db = self.mongo.db

        except:
            print("mongo db doesn't exist")
            return False
        
        self.time_db_tracker_records = self.mongo.db.records
        self.time_db_tracker_imports = self.mongo.db.imports
        self.time_db_tracker_admin = self.mongo.db.admin

        collection_names= set(self.mongo.db.list_collection_names())

        record_cnt = 0
        for doc in self.time_db_tracker_records.find():
            record_cnt += 1
            user_name = self.test_acc
            if "user" in doc:
                user_name = doc['user']
            self.users.add(user_name)

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
            self.topup_minutes  = self.WEEKEND_REWARD_CONS_MINUTES

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


    def retrieve_admin_stat(self, user_name):

        is_success = ['Success', 'Fail']
        actions = [AdminAction.Pause.name, AdminAction.Unpause.name, AdminAction.wifion.name]
        current_date = datetime.today() 
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


    def retrieve_for_time_stat(self, start, end, user_name):

        # parallel array
        # date_range->['2021-x-y', '2021-x-y', '2021-x-y']
        # used->[0, 0, 0]
        # added->[0,0,0]
        num_of_days = 14
        date_range = [(datetime.today()+timedelta(days=-i)).strftime('%Y-%m-%d') for i in range(0, num_of_days)]
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



import flask_pymongo
from flask_pymongo import PyMongo
from datetime import datetime, timedelta

from enum import Enum

AdminAction = Enum('AdminAction', 'Pause Unpause wifion')

class TimeKeeperDao:
    def __init__(self, app):
        self.remaining_minutes = 0
        self.topup_minutes = 0
        self.used_minutes = 0
        self.input_lines = set()

        self.time_keeper_db_name = "testtimedb"

        self.mongo = PyMongo(app)
        self.time_db_tracker_records = None
        self.time_db_tracker_imports = None
        self.time_db_tracker_admin = None

        self.WEEKEND_REWARD_CONS_MINUTES = 35 # a one-off 35 minutes reward on Friday/Saturday/Sunday
        self.INIT_RECORD_TABLE_PAYLOAD = {"datetime":datetime.fromtimestamp(0), 'minutesUsed':[], 'minutesAdded':[self.WEEKEND_REWARD_CONS_MINUTES]}
        self.INIT_ADMIN_TABLE_PAYLOAD = {"datetime":datetime.fromtimestamp(0), 'action':AdminAction.Unpause.name, 'is_success':False}
        self.INIT_IMPORTS_TABLE_PAYLOAD = {"loglin":f"1970-01-01,topup,{self.WEEKEND_REWARD_CONS_MINUTES}"}

        self.db_exist = self.init_with_db()



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

        record_cnt = 0
        for doc in self.time_db_tracker_records.find():
            record_cnt += 1
            if 'minutesUsed' in doc:
                self.used_minutes += sum(doc['minutesUsed'])
            if 'minutesAdded' in doc:
                self.topup_minutes += sum(doc['minutesAdded'])
        # if the table doesn't exist, initialize it with some number of minutes
        if record_cnt == 0:
            self.time_db_tracker_records.insert_one(self.INIT_RECORD_TABLE_PAYLOAD)
            self.time_db_tracker_admin.insert_one(self.INIT_ADMIN_TABLE_PAYLOAD)
            self.time_db_tracker_imports.insert_one(self.INIT_IMPORTS_TABLE_PAYLOAD)
            self.topup_minutes  = self.WEEKEND_REWARD_CONS_MINUTES

            self.time_db_tracker_records.create_index([("datetime", flask_pymongo.DESCENDING)], unique=True, name="datetimeIdx")
            self.time_db_tracker_admin.create_index([("datetime", flask_pymongo.DESCENDING)], unique=True, name="datetimeIdx")
        self.remaining_minutes = self.topup_minutes - self.used_minutes
        return True


    def retrieve_admin_stat(self):

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


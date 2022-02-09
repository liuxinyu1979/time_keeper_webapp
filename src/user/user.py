from flask import Flask, jsonify
import flask_pymongo
from flask_pymongo import PyMongo
from datetime import datetime
from bson.objectid import ObjectId


class User():

    def __init__(self, app, time_keeper_dao):
        self.mongo = PyMongo(app)
        self.time_db_tracker_accounts = self.mongo.db.accounts
        self.time_keeper_dao = time_keeper_dao

        try:
            cx = self.mongo.cx.server_info()
            db = self.mongo.db

        except:
            print("Log: mongo db doesn't exist")
            return False

        self.INIT_ACCOUNTS_TABLE_PAYLOAD = {"name": "test","email": "test@au4tech.com","password": "", "created_on":datetime.fromtimestamp(0), "updated_on":datetime.fromtimestamp(0)}
        collection_names= set(self.mongo.db.list_collection_names())
        if "accounts" not in collection_names:
            self.time_db_tracker_accounts.insert_one(self.INIT_ACCOUNTS_TABLE_PAYLOAD)
            self.time_db_tracker_accounts.create_index([("name", flask_pymongo.DESCENDING)], unique=True, name="loginNameIdx")


    def acc_name_exist(self, acc_name):
        if self.time_db_tracker_accounts.find_one({'name':acc_name}):
            return True
        return False
    
    def get_user(self, acc_name):
        return self.time_db_tracker_accounts.find_one({'name':acc_name})

    def signup(self, acc_name, email, password):
        time_now = datetime.now()
        new_acc = {
            "name": acc_name,
            "email": email,
            "password": password,
            "created_on": time_now,
            "updated_on": time_now
        }

        if self.acc_name_exist(acc_name):
            return jsonify({"error":"account already exist"}), 400
        self.time_db_tracker_accounts.insert_one(new_acc)
        # Award a 35 minutes as signup bonus 
        self.time_keeper_dao.init_time_vals_for_user(acc_name, 0, 35)
        acc_in_db = self.time_db_tracker_accounts.find_one({'name':acc_name}) 
        return acc_in_db

    def update_account_info(self, acc_name, email):
        time_now = datetime.now()
        if not self.acc_name_exist(acc_name):
            return False, {"error":"account does not exist"}

        self.time_db_tracker_accounts.update_one({"name":acc_name}, {'$set': {'email':email, "updated_on":time_now}}, upsert=True)
        return True, {}

    def update_account_secret(self, acc_name, password):
        time_now = datetime.now()
        if not self.acc_name_exist(acc_name):
            return False, {"error":"account does not exist"}

        self.time_db_tracker_accounts.update_one({"name":acc_name}, {'$set': {'password':password, "updated_on":time_now}}, upsert=True)
        return True, {}
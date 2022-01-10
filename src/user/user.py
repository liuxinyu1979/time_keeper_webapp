from flask import Flask, jsonify
import flask_pymongo
from flask_pymongo import PyMongo
from datetime import datetime

class User:

    def __init__(self, app):
        self.mongo = PyMongo(app)
        self.time_db_tracker_accounts = self.mongo.db.accounts

        try:
            cx = self.mongo.cx.server_info()
            db = self.mongo.db

        except:
            print("mongo db doesn't exist")
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

        acc_in_db = self.time_db_tracker_accounts.find_one({'name':acc_name}) 
        del acc_in_db['_id']
        return jsonify(acc_in_db), 200
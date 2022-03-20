from flask import Flask
from config import DevConfig
from flask_pymongo import PyMongo

def create_app(test_config=None):
    # create and configure the app
    qooqoo_app = Flask(__name__)
    mongo_client = None
    if test_config is None:
        # load the instance config, if it exists, when not testing
        qooqoo_app.config.from_object(DevConfig)
        mongo_client = PyMongo(qooqoo_app)

        try:
            cx = mongo_client.cx.server_info()
            db = mongo_client.db

        except:
            print("Log: mongo db doesn't exist")
            return None, None


    else:
        # load the test config if passed in
        qooqoo_app.config.from_mapping(test_config)
        mongo_client = PyMongo(qooqoo_app)

    return qooqoo_app, mongo_client

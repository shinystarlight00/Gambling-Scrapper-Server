from dotenv import load_dotenv
import pymongo
import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))

class DB:
    def __init__(self, web):
        # Load .env
        self.env = load_dotenv(dotenv_path=os.path.join(BASEDIR, '../.env'))

        # Load DB Client
        self.client = pymongo.MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["scraper"]
        self.web = web

    def col(self, name):
        return self.db[self.web + "_" + name]

    def getOne(self, name):
        obj = self.col(name).find_one()
        if (obj == None): return {}
        return obj
    
    def getOneBy(self, name, filter):
        obj = self.col(name).find_one(filter)
        if (obj == None): return {}
        return obj

    def getMany(self, name):
        arr = list(self.col(name).find())
        if (arr == None): return []
        return arr
    
    def getLastN(self, name, n, value = None):
        if (not value): arr = list(self.col(name).find().sort([("$natural", -1 )]).limit(n))
        else:
            obj = {}; obj[value] = 1
            arr = list(self.col(name).find({}, obj).sort([("$natural", -1 )]).limit(n))
        if (arr == None): return []
        return arr

    def update(self, name, first, second):
        self.col(name).update_one(first, { "$set": second }, upsert=True)

    def insertMany(self, name, arr):
        self.col(name).insert_many(arr)

    def insertOne(self, name, obj):
        self.col(name).insert_one(obj)
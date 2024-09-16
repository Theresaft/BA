from pymongo import MongoClient
MONGO_URI = 'mongodb://mongoDB:27017/my_database'
client = MongoClient(MONGO_URI)
db = client.get_database()

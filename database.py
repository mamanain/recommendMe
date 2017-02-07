import pymongo


class DataBase:

    def __init__(self, db_name, address="localhost", port=27017):
        client = pymongo.MongoClient(address, port)
        self._db = client[db_name]

    def insert_one(self, document, collection_name):
        collection = self._db[collection_name]
        collection.insert_one(document)

    def insert_many(self, documents, collection_name):
        collection = self._db[collection_name]
        collection.insert_many(documents)

    def get_one(self, _id, collection_name):
        collection = self._db[collection_name]
        return collection.find_one({"_id": _id})

    def get_all(self, collection_name):
        collection = self._db[collection_name]
        return collection.find()

    def get_collection_size(self, collection_name):
        return self._db[collection_name].count()

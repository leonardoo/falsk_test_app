from abc import ABC, abstractmethod
from extensions import mongo


class DatabaseOperations(ABC):

    @abstractmethod
    def add_balance(self, user_id, money):
        pass

    @abstractmethod
    def find_account(self, user_id):
        pass


class DataBaseDummy(DatabaseOperations):

    def __init__(self):
        self.accounts = {}

    def add_account(self, user_id, pin, balance):
        self.accounts[user_id] = {
            "pin": pin,
            "balance": balance
        }

    def add_balance(self, user_id, money):
        self.accounts[user_id]["balance"] += money

    def find_account(self, user_id):
        return self.accounts.get(user_id, None)


class DatabaseMongo(DatabaseOperations):

    def __init__(self):
        self.db = mongo.db

    def add_account(self, user_id, pin, balance):
        self.db.accounts.insert_one({
            "user_id": user_id,
            "pin": pin,
            "balance": balance
        })

    def add_balance(self, user_id, money):
        self.db.accounts.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": money}}
        )

    def find_account(self, user_id):
        return self.db.accounts.find_one({"user_id": user_id})

import os
import json
from pathlib import Path

from pymongo import MongoClient

client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/acme"))
db = client.acme
path = str(Path(__file__).parent.joinpath("./initial_data.json").absolute())

with open(path, "r") as f:
    json_data = json.loads(f.read())
    for data in json_data:
        find = {
            "user_id": data["user_id"], "pin": data["pin"]
        }
        if db.accounts.count_documents(find) == 0:
            db.accounts.insert_one(data)

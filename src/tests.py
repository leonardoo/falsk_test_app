from io import StringIO
from unittest import TestCase
from unittest.mock import patch
import json

from business import Builder, BaseStep
from datahandler import DataBaseDummy, DatabaseMongo
from streamhandler import StreamHandlerDummy
from create_app import create_app
from extensions import mongo


class TestManager(TestCase):

    def setUp(self):
        self.db = DataBaseDummy()
        self.db.add_account("123", "123", 1000000)
        self.stream = StreamHandlerDummy()

    def test_manager_one_step(self):

        with open("./data/json_one_step.json", "r") as f:
            json_data = json.loads(f.read())
            builder = Builder(json_data, self.stream)
            manager = builder.generate_manager(self.db)
            actions = list(manager.actions.items())
            self.assertEqual(len(actions), 2)
            for name, action in manager.actions.items():
                self.assertIsInstance(
                    action, BaseStep
                )

    def test_manager_one_step_execution(self):
        with open("./data/json_one_step.json", "r") as f:
            json_data = json.loads(f.read())
            builder = Builder(json_data, self.stream)
            manager = builder.generate_manager(self.db)
            manager.execute()
            step = manager.actions["validate_account"]
            self.assertFalse(
                step.action_resolver.is_valid
            )

    @patch("action.WithdrawalMoneyDollars._get_dollar_value", return_value=2)
    def test_manager_step_execution(self, mock_dollar):
        self.db.add_account("105398891", 2090, 1_000_000)
        with open("./data/json_complete.json", "r") as f:
            json_data = json.loads(f.read())
            builder = Builder(json_data, self.stream)
            manager = builder.generate_manager(self.db)
            manager.execute()
            self.assertEqual(
                self.db.accounts["105398891"]["balance"],
                999_940
            )

    @patch("action.WithdrawalMoneyDollars._get_dollar_value", return_value=2)
    def test_manager_step_execution_le(self, mock_dollar):
        self.db.add_account("105398891", 2090, 50_000)
        with open("./data/json_complete.json", "r") as f:
            json_data = json.loads(f.read())
            builder = Builder(json_data, self.stream)
            manager = builder.generate_manager(self.db)
            manager.execute()
            self.assertEqual(
                self.db.accounts["105398891"]["balance"],
                250_000
            )

    @patch("action.WithdrawalMoneyDollars._get_dollar_value", return_value=2)
    def test_manager_step_execution_more_50k(self, mock_dollar):
        self.db.add_account("105398891", 2090, 51_000)
        with open("./data/json_complete.json", "r") as f:
            json_data = json.loads(f.read())
            builder = Builder(json_data, self.stream)
            manager = builder.generate_manager(self.db)
            manager.execute()
            self.assertEqual(
                self.db.accounts["105398891"]["balance"],
                151_000
            )


class TestFlaskApp(TestCase):

    def setUp(self):
        self.app = create_app(testing=True)
        self.client = self.app.test_client()

    def tearDown(self):
        mongo.db.accounts.delete_many({})

    def test_manager_one_step(self):
        with open("./data/json_one_step.json", "rb") as f:
            name = "json_complete.json"
            data = {
                'file': (f, name)
            }
            response = self.client.post('/process_json', data=data)
            json_data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertDictEqual(
                json_data,
                {
                    "status": 'File Processed'
                }
            )

    def test_manager_invalid_file(self):
        with open("./data/load_initial_data.py", "rb") as f:
            name = "json_complete.json"
            data = {
                'file': (f, name)
            }
            response = self.client.post('/process_json', data=data)
            json_data = response.get_json()
            self.assertEqual(response.status_code, 400)
            self.assertDictEqual(
                json_data,
                {
                    "status": 'Invalid Schema'
                }
            )

    @patch("action.WithdrawalMoneyDollars._get_dollar_value", return_value=2)
    def test_manager_complete(self, dollar_mock):
        DatabaseMongo().add_account("105398891", 2090, 1_000_000)
        user_id = "105398891"
        with open("./data/json_complete.json", "rb") as f:
            name = "json_complete.json"
            data = {
                'file': (f, name)
            }
            response = self.client.post('/process_json', data=data)
            json_data = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertDictEqual(
                json_data,
                {
                    "status": 'File Processed'
                }
            )
            account = mongo.db.accounts.find_one({"user_id": "105398891"})
            self.assertEqual(
                account["balance"],
                999_940
            )

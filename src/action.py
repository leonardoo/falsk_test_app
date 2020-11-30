from abc import ABC, abstractmethod
import operator
from datetime import date, timedelta
import requests


class Action(ABC):
    subclasses = {}
    action_id = None

    OPERATORS = {
        "lte": operator.le,
        "lt": operator.lt,
        "gt": operator.gt,
        "gte": operator.ge,
        "eq": operator.eq,
    }

    def __init__(self, database):
        self.database = database

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.subclasses[cls.action_id] = cls

    @classmethod
    def get_action(cls, action_id):
        return cls.subclasses[action_id]

    @abstractmethod
    def action(self, *args, **kwargs):
        pass

    def condition_resolver(self, field, operator, value):
        action_value = getattr(self, field)
        operation = self.OPERATORS.get(operator)
        return operation(action_value, value)


class ValidateAccount(Action):

    action_id = "validate_account"

    def action(self, user_id=None, pin=None):
        account = self.database.find_account(user_id)
        self.is_valid = bool(account and account["pin"] == pin)


class CheckBalance(Action):

    action_id = "get_account_balance"

    def _get_balance(self, user_id):
        account = self.database.find_account(user_id)
        if not account:
            raise Exception("account dont exists")
        return account["balance"]

    def action(self, user_id=None, **kwargs):
        self.user_id = user_id
        return self.balance

    @property
    def balance(self):
        return self._get_balance(self.user_id)


class DepositMoney(Action):

    action_id = "deposit_money"

    def action(self, user_id=None, money=None):
        self.database.add_balance(user_id, money)


class WithdrawalMoneyPesos(CheckBalance):

    action_id = "withdraw_in_pesos"

    def _decrease_balance(self, user_id=None, money=None):
        balance = self._get_balance(user_id)
        if balance < money:
            raise Exception("insufficient funds")
        self.database.add_balance(user_id, money * -1)

    def action(self, user_id=None, money=None, **kwargs):
        self._decrease_balance(user_id, money)


class WithdrawalMoneyDollars(WithdrawalMoneyPesos):
    action_id = "withdraw_in_dollars"

    def _get_dollar_value(self):
        day = date.today()
        data = []
        while not data:
            data = self._request_dollar_value(day.strftime('%Y-%m-%d'))
            day -= timedelta(days=1)
        return float(data[0]["valor"])

    def _request_dollar_value(self, day):
        response = requests.get(
            f"https://www.datos.gov.co/resource/ceyp-9c7c.json?VIGENCIADESDE={day}")
        response.raise_for_status()
        return response.json()

    def _decrease_balance(self, user_id=None, money=None):
        money *= self._get_dollar_value()
        super()._decrease_balance(user_id, money)


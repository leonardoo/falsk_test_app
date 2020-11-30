import json
from copy import copy
from pathlib import Path

from action import Action

from jsonschema import validate


class BaseStep:

    def __init__(self, data):
        self.params = data["params"]
        self.transactions = data["transitions"]
        self.id = data["id"]
        self.has_action = True

    def resolve_parameter(self, param_id):
        return self.params[param_id]


class Trigger(BaseStep):
    
    def __init__(self, trigger_data):
        super().__init__(trigger_data)
        self.has_action = False


class Step(BaseStep):

    def __init__(self, step_data, db):
        super().__init__(step_data)
        self.action = step_data["action"]
        ActionResolver = Action.get_action(self.action)
        self.action_resolver = ActionResolver(db)

    def do_action(self, *args, **kwargs):
        self.action_resolver.action(**kwargs)

    def validate_condition(self, field_id, operator, value):
        return self.action_resolver.condition_resolver(field_id, operator, value)


class Manager:
    
    def __init__(self, steps, triggers, stream_handler):
        self.steps = steps
        self.triggers = triggers
        self.actions = copy(steps)
        self.actions.update(triggers)
        self.stream_handler = stream_handler

    def get_action_value(self, action_id, param_id):
        action = self.actions[action_id]
        return action.resolve_parameter(param_id)

    def resolve_parameters(self, step):
        if isinstance(step, Trigger):
            return step.params

        params_resolved = {}
        for name, parameter in step.params.items():
            action_id = parameter["from_id"]
            if action_id:
                param_id = parameter["param_id"]
                value = self.get_action_value(action_id, param_id)
            else:
                value = parameter["value"]
            params_resolved[name] = value
        return params_resolved

    def execute_step(self, step):
        self.stream_handler.send(f"Executing Step {step.id}", "ok")
        params = self.resolve_parameters(step)
        if step.has_action:
            self.stream_handler.send(f"Executing Step Actions for {step.id}", "ok")
            step.do_action(**params)
        
    def get_next_transaction(self, step):
        self.stream_handler.send(f"Executing transactions on Step {step.id}", "ok")
        transactions = step.transactions
        is_valid_transaction = False
        target = None
        while not is_valid_transaction and len(transactions) > 0:
            transaction = transactions.pop(0)
            target = transaction["target"]
            is_valid_transaction = self.execute_transaction(transaction)
        return target if is_valid_transaction else None

    def execute_transaction(self, transaction):
        self.stream_handler.send(f"Executing transactions for target {transaction['target']}", "ok")
        if not transaction["condition"]:
            return True
        for condition in transaction["condition"]:
            action_id = condition.pop("from_id")
            self.stream_handler.send(f"check Condition {action_id} -> {condition['field_id']} {condition['operator']} {condition['value']}", "ok")
            action = self.actions[action_id]
            if not action.validate_condition(**condition):
                self.stream_handler.send(f"Condition: False", "ok")
                return False
            self.stream_handler.send(f"Condition: True", "ok")
        return True

    def execute(self):
        self.stream_handler.send("Initial Step", "ok")
        step = self.actions["start"]
        try:
            while step:
                self.execute_step(step)
                target_step = self.get_next_transaction(step)
                if target_step:
                    self.stream_handler.send(f"Next Step Found {target_step}", "ok")
                    step = self.actions[target_step]
                else:
                    self.stream_handler.send("Next Step Not Found", "ok")
                    break
        except Exception as e:
            self.stream_handler.send(f"An exception as occurred {str(e)}", "error")
        self.stream_handler.send("Finish Execution", "ok")


class Builder:
    
    def __init__(self, json_data, stream_handler):
        self.json_data = json_data
        self.stream_handler = stream_handler
        self.validate()

    def validate(self):
        with open(Path(__file__).parent.joinpath("./data/jsonschema.json",), "r") as f:
            schema = json.loads(f.read())
        validate(instance=self.json_data, schema=schema)

    def generate_manager(self, db):
        steps = {}
        triggers = {}
        for step_data in self.json_data["steps"]:
            step = Step(step_data, db)
            steps[step.id] = step

        trigger = Trigger(self.json_data["trigger"])
        triggers[trigger.id] = trigger

        return Manager(steps, triggers, self.stream_handler)



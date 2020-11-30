from abc import ABC, abstractmethod

from extensions import socketio


class StreamHandlerBase(ABC):

    @abstractmethod
    def send(self, msg, status):
        pass

class StreamHandlerDummy(StreamHandlerBase):

    def __init__(self):
        self.messages = []

    def send(self, msg, status):
        self.messages.append({
            "msg": msg,
            "status": status
        })


class StreamHandlerSocketIO(StreamHandlerBase):

    def __init__(self):
        self.sender = socketio

    def send(self, msg, status):
        socketio.emit("event", {"event": msg, "status": status})
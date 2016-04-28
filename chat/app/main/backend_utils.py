__author__ = 'anushabala'


class FinishedSession(object):
    def __init__(self, message, num_seconds, mturk_code=None):
        self.message = message
        self.num_seconds = num_seconds
        self.mturk_code = mturk_code


class WaitingSession(object):
    def __init__(self, message, num_seconds):
        if message and len(message) > 0:
            self.message = message
        else:
            self.message = "Generating image for car commands task"
        self.num_seconds = num_seconds


class SingleTaskSession(object):
    def __init__(self, scenario, agent_index, num_seconds):
        self.scenario = scenario
        self.agent_index = agent_index
        self.agent_info = scenario["agents"][agent_index]
        self.num_seconds = num_seconds


class UserChatSession(object):
    def __init__(self, room_id, agent_index, scenario, num_seconds):
        self.room_id = room_id
        self.agent_index = agent_index
        self.scenario = scenario
        self.agent_info = scenario["agents"][agent_index]
        self.num_seconds = num_seconds

    def to_dict(self):
        return {"room": self.room_id,
                "agent_index": self.agent_index,
                "scenario": self.scenario,
                "agent_info": self.agent_info,
                "num_seconds": self.num_seconds}
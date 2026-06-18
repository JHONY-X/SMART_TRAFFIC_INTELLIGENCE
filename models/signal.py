from utils.constants import Constants

class Signal:
    def __init__(self, lane_name):
        self.lane_name = lane_name
        self.state = Constants.RED
        self.timer = 0
        self.max_green_time = Constants.DEFAULT_BASE_GREEN_TIME

    def set_state(self, new_state, duration):
        self.state = new_state
        self.timer = duration

    def tick(self, seconds=1):
        if self.timer > 0:
            self.timer -= seconds
            if self.timer < 0:
                self.timer = 0
        return self.timer

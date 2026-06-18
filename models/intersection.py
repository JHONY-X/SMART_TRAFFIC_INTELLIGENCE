from models.lane import Lane
from models.signal import Signal

class Intersection:
    def __init__(self, id, lane_config):
        """
        lane_config: dict with direction as key and number of lanes as value
        e.g., {"North": 3, "South": 3, "East": 1, "West": 1}
        """
        self.id = id
        self.lanes = {}
        self.signals = {}
        self.reconfigure(lane_config)

    def reconfigure(self, lane_config):
        self.lanes = {}
        self.signals = {}
        for direction, count in lane_config.items():
            for i in range(1, count + 1):
                lane_id = f"{direction}-{i}"
                self.lanes[lane_id] = Lane(lane_id)
                self.signals[lane_id] = Signal(lane_id)
        
        self.active_lane = None
        self.all_red_timer = 0

    def get_lane(self, name):
        return self.lanes.get(name)

    def get_signal(self, name):
        return self.signals.get(name)

    def get_all_lanes(self):
        return list(self.lanes.values())
        
    def get_all_signals(self):
        return list(self.signals.values())

from utils.constants import Constants

class SignalController:
    def __init__(self, config):
        self.base_green_time = config.get("base_green_time", Constants.DEFAULT_BASE_GREEN_TIME)
        self.max_green_time = config.get("max_green_time", 60)
        
    def calculate_green_time(self, vehicle_count, factor=2):
        """
        Green_time = base_time + (cars x factor)
        """
        calculated_time = self.base_green_time + (vehicle_count * factor)
        return min(calculated_time, self.max_green_time)

    def set_signal(self, intersection, active_direction, duration):
        """
        Sets all lanes in the active direction to Green, others to Red.
        """
        for signal in intersection.get_all_signals():
            if signal.lane_name.startswith(active_direction):
                signal.set_state(Constants.GREEN, duration)
            else:
                signal.set_state(Constants.RED, 0)
        intersection.active_lane = active_direction

    def set_yellow(self, intersection, direction, duration):
        """
        Sets all lanes in the direction to Yellow.
        """
        for signal in intersection.get_all_signals():
            if signal.lane_name.startswith(direction):
                signal.set_state(Constants.YELLOW, duration)
        
    def set_all_red(self, intersection):
        for signal in intersection.get_all_signals():
            signal.set_state(Constants.RED, 0)
        intersection.active_lane = None

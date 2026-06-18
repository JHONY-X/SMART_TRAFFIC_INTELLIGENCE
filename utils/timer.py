import time

class SimulationTimer:
    def __init__(self, speed_multiplier=1.0):
        self.current_time = 0
        self.speed_multiplier = speed_multiplier

    def tick(self, seconds=1):
        """Advance the simulation time."""
        self.current_time += seconds
        # time.sleep(seconds / self.speed_multiplier)  # Actual sleep if we wanted real-time simulation

    def get_time(self):
        return self.current_time

    def reset(self):
        self.current_time = 0

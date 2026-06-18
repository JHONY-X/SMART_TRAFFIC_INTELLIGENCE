class InputHandler:
    def __init__(self, environment):
        self.environment = environment

    def get_traffic_data(self):
        """
        Cleans and aggregates input from the environment.
        In a real scenario, this would read from sensors.
        Here it reads from the simulation state.
        """
        data = {}
        for intersection in self.environment.intersections:
            data[intersection.id] = {}
            for lane in intersection.get_all_lanes():
                data[intersection.id][lane.name] = {
                    "count": lane.get_vehicle_count(),
                    "density": lane.get_density(),
                    "max_wait_time": lane.get_max_waiting_time(self.environment.timer.get_time()),
                    "has_emergency": lane.has_emergency_vehicle()
                }
        return data

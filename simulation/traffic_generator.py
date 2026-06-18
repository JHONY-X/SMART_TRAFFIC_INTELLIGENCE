import random
from models.vehicle import Vehicle

class TrafficGenerator:
    def __init__(self, environment):
        self.environment = environment
        self.vehicle_id_counter = 0
        self.intensity = 0.3 # default

    def set_intensity(self, intensity_val):
        """intensity_val is 0-100, we map it to 0.0-0.6 probability"""
        self.intensity = (float(intensity_val) / 100.0) * 0.6

    def generate_random_traffic(self, emergency_prob=0.01):
        """
        Randomly generates cars based on current intensity
        """
        current_time = self.environment.timer.get_time()
        for intersection in self.environment.intersections:
            for lane in intersection.get_all_lanes():
                if random.random() < self.intensity:
                    self.vehicle_id_counter += 1
                    is_emer = random.random() < emergency_prob
                    v = Vehicle(f"V{self.vehicle_id_counter}", current_time, is_emergency=is_emer)
                    lane.add_vehicle(v)
                    
    def simulate_test_case_1(self, intersection_id, target_direction):
        """Heavy traffic in one direction (all lanes)"""
        current_time = self.environment.timer.get_time()
        for intx in self.environment.intersections:
            if intx.id == intersection_id:
                # Find all lanes for this direction
                lanes = [l for name, l in intx.lanes.items() if name.startswith(target_direction)]
                for lane in lanes:
                    for _ in range(5): # 5 cars per lane
                        self.vehicle_id_counter += 1
                        lane.add_vehicle(Vehicle(f"V{self.vehicle_id_counter}", current_time))
                    
    def simulate_test_case_3(self, intersection_id, target_direction):
        """Emergency vehicle in a direction (lane 1)"""
        current_time = self.environment.timer.get_time()
        for intx in self.environment.intersections:
            if intx.id == intersection_id:
                lane = intx.get_lane(f"{target_direction}-1")
                if lane:
                    self.vehicle_id_counter += 1
                    lane.add_vehicle(Vehicle(f"V{self.vehicle_id_counter}", current_time, is_emergency=True))

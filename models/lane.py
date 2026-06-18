class Lane:
    def __init__(self, name, capacity=50):
        self.name = name
        self.capacity = capacity
        self.vehicles = []

    def add_vehicle(self, vehicle):
        if len(self.vehicles) < self.capacity:
            self.vehicles.append(vehicle)
            return True
        return False

    def remove_vehicle(self):
        if self.vehicles:
            return self.vehicles.pop(0)
        return None

    def get_vehicle_count(self):
        return len(self.vehicles)

    def get_density(self):
        return self.get_vehicle_count() / self.capacity if self.capacity > 0 else 0

    def has_emergency_vehicle(self):
        return any(v.is_emergency for v in self.vehicles)

    def get_max_waiting_time(self, current_time):
        if not self.vehicles:
            return 0
        return max(v.get_waiting_time(current_time) for v in self.vehicles)

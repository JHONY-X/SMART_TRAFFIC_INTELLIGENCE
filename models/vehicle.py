class Vehicle:
    def __init__(self, id, arrival_time, is_emergency=False):
        self.id = id
        self.arrival_time = arrival_time
        self.is_emergency = is_emergency

    def get_waiting_time(self, current_time):
        return current_time - self.arrival_time

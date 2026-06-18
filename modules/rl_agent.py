import json
import random
import os
from utils.constants import Constants

class RLAgent:
    def __init__(self, q_table_path="data/q_table.json"):
        self.q_table_path = q_table_path
        self.q_table = {}
        self.actions = ["North", "East", "South", "West"]
        self.load_q_table()

    def get_state(self, traffic_data, intersection_id):
        """
        Discretizes vehicle counts for North, East, South, West.
        State representation: (bin_N, bin_E, bin_S, bin_W)
        """
        if intersection_id not in traffic_data:
            return (0, 0, 0, 0)
        
        lanes = traffic_data[intersection_id]
        counts = {"North": 0, "East": 0, "South": 0, "West": 0}
        
        for lane_name, metrics in lanes.items():
            direction = lane_name.split('-')[0]
            if direction in counts:
                counts[direction] += metrics['count']
                
        # Discretize counts into bins:
        # 0: empty
        # 1: 1-2 vehicles
        # 2: 3-5 vehicles
        # 3: 6+ vehicles
        def discretize(c):
            if c == 0: return 0
            if c <= 2: return 1
            if c <= 5: return 2
            return 3
            
        state = (
            discretize(counts["North"]),
            discretize(counts["East"]),
            discretize(counts["South"]),
            discretize(counts["West"])
        )
        return state

    def get_q_values(self, state):
        state_key = str(state)
        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0] * len(self.actions)
        return self.q_table[state_key]

    def choose_action(self, state, epsilon=0.1):
        """
        Epsilon-greedy action selection.
        """
        if random.random() < epsilon:
            return random.randint(0, len(self.actions) - 1)
        
        q_vals = self.get_q_values(state)
        max_q = max(q_vals)
        # Handle ties randomly
        max_indices = [i for i, q in enumerate(q_vals) if q == max_q]
        return random.choice(max_indices)

    def update(self, state, action_idx, reward, next_state, alpha=0.1, gamma=0.9):
        """
        Q-learning update rule: Q(s,a) = Q(s,a) + alpha * (reward + gamma * max Q(s',a') - Q(s,a))
        """
        state_key = str(state)
        q_vals = self.get_q_values(state)
        next_q_vals = self.get_q_values(next_state)
        
        target = reward + gamma * max(next_q_vals)
        q_vals[action_idx] += alpha * (target - q_vals[action_idx])
        self.q_table[state_key] = q_vals

    def infer_next_states(self, traffic_data, environment):
        """
        Inference interface for running the simulator using the trained RL model.
        Returns a dict of decisions per intersection.
        """
        decisions = {}
        for intersection in environment.intersections:
            # Check if there is an emergency vehicle first (safety override)
            has_emergency = False
            emergency_lane = None
            for lane in intersection.get_all_lanes():
                if lane.has_emergency_vehicle():
                    has_emergency = True
                    emergency_lane = lane.name
                    break
            
            if has_emergency:
                decisions[intersection.id] = {"type": "emergency", "target_lane": emergency_lane}
                continue

            state = self.get_state(traffic_data, intersection.id)
            # Epsilon = 0 for pure exploitation during production inference
            action_idx = self.choose_action(state, epsilon=0.0)
            target_direction = self.actions[action_idx]
            
            # Formulate decision as a greedy switch to the target direction
            target_lane = f"{target_direction}-1"
            decisions[intersection.id] = {"type": "greedy", "target_lane": target_lane}
            
        return decisions

    def save_q_table(self):
        os.makedirs(os.path.dirname(self.q_table_path), exist_ok=True)
        with open(self.q_table_path, 'w') as f:
            json.dump(self.q_table, f, indent=2)

    def load_q_table(self):
        if os.path.exists(self.q_table_path):
            try:
                with open(self.q_table_path, 'r') as f:
                    self.q_table = json.load(f)
            except Exception as e:
                print(f"Error loading Q-table: {e}")
                self.q_table = {}

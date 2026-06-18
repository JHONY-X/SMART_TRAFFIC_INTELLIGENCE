import json
from utils.constants import Constants

class RuleEngine:
    def __init__(self, rules_file_path):
        self.rules = self._load_rules(rules_file_path)

    def _load_rules(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading rules: {e}")
            return []

    def evaluate(self, traffic_data):
        """
        Evaluates conditions and returns a list of triggered actions.
        This handles the Fuzzy Logic concepts (e.g. HIGH traffic, LONG wait time).
        """
        triggered_actions = []
        for int_id, lanes in traffic_data.items():
            # Find the max waiting time and highest density across all lanes
            highest_density_lane = None
            max_density = -1
            max_wait_time = 0
            has_emergency = False
            total_density = 0
            
            for lane_name, metrics in lanes.items():
                total_density += metrics['density']
                if metrics['density'] > max_density:
                    max_density = metrics['density']
                    highest_density_lane = lane_name
                
                if metrics['max_wait_time'] > max_wait_time:
                    max_wait_time = metrics['max_wait_time']
                    
                if metrics['has_emergency']:
                    has_emergency = True
            
            # Forward Chaining: Apply rules to facts
            intersection_actions = []
            for rule in sorted(self.rules, key=lambda x: x['priority'], reverse=True):
                condition = rule['condition']
                
                if condition == "emergency_vehicle" and has_emergency:
                    intersection_actions.append({"action": rule['action'], "priority": rule['priority'], "intersection_id": int_id})
                    break # Override, stop evaluating lower priority rules
                    
                elif condition == "max_wait_time_exceeded" and max_wait_time > Constants.DEFAULT_MAX_WAIT_TIME:
                    intersection_actions.append({"action": rule['action'], "priority": rule['priority'], "intersection_id": int_id})
                    
                elif condition == "highest_density" and highest_density_lane is not None and max_density > 0:
                    intersection_actions.append({"action": rule['action'], "target_lane": highest_density_lane, "priority": rule['priority'], "intersection_id": int_id})
                    
                elif condition == "no_traffic" and total_density == 0:
                    intersection_actions.append({"action": rule['action'], "priority": rule['priority'], "intersection_id": int_id})
            
            triggered_actions.extend(intersection_actions)
        return triggered_actions

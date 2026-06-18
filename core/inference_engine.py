from modules.emergency_handler import EmergencyHandler

class InferenceEngine:
    def __init__(self, rule_engine):
        self.rule_engine = rule_engine

    def infer_next_states(self, traffic_data, current_states):
        """
        Uses forward chaining. Continuous evaluation.
        Combines Greedy Algorithm, Priority Scheduling, and Round Robin.
        """
        actions = self.rule_engine.evaluate(traffic_data)
        decisions = {}
        
        # Group actions by intersection
        int_actions = {}
        for action in actions:
            int_id = action['intersection_id']
            if int_id not in int_actions:
                int_actions[int_id] = []
            int_actions[int_id].append(action)

        for int_id, lanes in traffic_data.items():
            decision = None
            
            # Check highest priority action for this intersection
            if int_id in int_actions and int_actions[int_id]:
                # Actions are already sorted by priority in RuleEngine
                top_action = int_actions[int_id][0]
                
                if top_action['action'] == 'emergency_override':
                    # Priority Scheduling
                    emergencies = EmergencyHandler.check_emergencies({int_id: lanes})
                    if emergencies:
                        # Pick the first lane with an emergency
                        target_lane = emergencies[0][1]
                        decision = {"type": "emergency", "target_lane": target_lane}
                        
                elif top_action['action'] == 'force_switch':
                    # Round Robin / Fallback
                    # Force switch to the next lane because wait time is too long
                    decision = {"type": "force_switch"}
                    
                elif top_action['action'] == 'prioritize_highest_density':
                    # Greedy Algorithm: Choose lane with max traffic
                    decision = {"type": "greedy", "target_lane": top_action['target_lane']}
                    
                elif top_action['action'] == 'reduce_cycle_time':
                    decision = {"type": "fast_cycle"}
            
            if not decision:
                # Default Round Robin
                decision = {"type": "round_robin"}
                
            decisions[int_id] = decision
            
        return decisions

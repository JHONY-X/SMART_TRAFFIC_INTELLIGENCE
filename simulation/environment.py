import json
import time
from utils.timer import SimulationTimer
from models.intersection import Intersection
from modules.input_handler import InputHandler
from modules.traffic_analyzer import TrafficAnalyzer
from modules.signal_controller import SignalController
from modules.sync_controller import SyncController
from core.rule_engine import RuleEngine
from core.inference_engine import InferenceEngine
from core.scheduler import Scheduler
from simulation.traffic_generator import TrafficGenerator
from modules.rl_agent import RLAgent

class Environment:
    RULES = ["SIGNALIZED", "RL_TRAINED", "RIGHT_PRIORITY", "PRIORITY_ROAD"]

    def __init__(self, config_path, rules_path):
        self.config = self._load_json(config_path)
        self.timer = SimulationTimer(speed_multiplier=self.config.get("simulation_speed", 1.0))
        self.current_rule = "SIGNALIZED"
        self.overrides = {} # {intersection_id: {lane_id: state}}
        
        # Initialize intersections with multi-lane support
        self.intersections = []
        for int_data in self.config.get("intersections", []):
            # Default to 2 lanes based on the typical aerial image
            # For simplicity, North/South are main, East/West are secondary
            lane_config = {
                "North": 2, "South": 2, "East": 2, "West": 2
            }
            self.intersections.append(Intersection(int_data["id"], lane_config))
            
        # Initialize modules and core components
        self.input_handler = InputHandler(self)
        self.traffic_analyzer = TrafficAnalyzer()
        self.signal_controller = SignalController(self.config)
        self.sync_controller = SyncController(self.intersections)
        
        self.rule_engine = RuleEngine(rules_path)
        self.inference_engine = InferenceEngine(self.rule_engine)
        self.rl_agent = RLAgent("data/q_table.json")
        self.scheduler = Scheduler(self, self.signal_controller)
        self.traffic_generator = TrafficGenerator(self)

    def _load_json(self, path):
        with open(path, 'r') as f:
            return json.load(f)

    def set_rule(self, rule_name):
        if rule_name in self.RULES:
            self.current_rule = rule_name
            # If not signalized, set all signals to GREEN/OFF (visual only) or YELLOW BLINK
            if rule_name != "SIGNALIZED":
                for intx in self.intersections:
                    for sig in intx.get_all_signals():
                        sig.set_state("GREEN", 9999) # Logic will handle yielding

    def reconfigure_lanes(self, main_lanes, secondary_lanes):
        for intx in self.intersections:
            lane_config = {
                "North": main_lanes, "South": main_lanes,
                "East": secondary_lanes, "West": secondary_lanes
            }
            intx.reconfigure(lane_config)

    def process_vehicles(self):
        """Logic for vehicles crossing the intersection based on rules"""
        for intx in self.intersections:
            passing_candidates = []
            for lane_id, lane in intx.lanes.items():
                if lane.get_vehicle_count() > 0:
                    passing_candidates.append(lane_id)
            
            # Sort candidates by waiting time to resolve ties and gridlock
            current_time = self.timer.get_time()
            passing_candidates.sort(key=lambda lid: intx.get_lane(lid).get_max_waiting_time(current_time), reverse=True)

            for lane_id in passing_candidates:
                lane = intx.get_lane(lane_id)
                direction = lane_id.split('-')[0]
                can_pass = False
                
                # Emergency vehicles always have priority if they are at the front
                if lane.vehicles[0].is_emergency:
                    can_pass = True
                
                elif self.current_rule == "SIGNALIZED":
                    signal = intx.get_signal(lane_id)
                    if signal.state == "GREEN":
                        can_pass = True
                
                elif self.current_rule == "RIGHT_PRIORITY":
                    right_hand_direction = {
                        "North": "East", "East": "South", "South": "West", "West": "North"
                    }
                    right_dir = right_hand_direction[direction]
                    # Check if any lane in the right direction has vehicles
                    has_right_traffic = any(intx.get_lane(f"{right_dir}-{i}").get_vehicle_count() > 0 
                                            for i in range(1, 10) if intx.get_lane(f"{right_dir}-{i}"))
                    
                    if not has_right_traffic:
                        can_pass = True
                    else:
                        # Gridlock resolution: if I've been waiting too long, I might go anyway
                        if lane.get_max_waiting_time(current_time) > 20:
                            can_pass = True
                
                elif self.current_rule == "PRIORITY_ROAD":
                    if direction in ["North", "South"]:
                        can_pass = True
                    else:
                        has_main_traffic = any(intx.get_lane(f"{d}-{i}").get_vehicle_count() > 0 
                                              for d in ["North", "South"] 
                                              for i in range(1, 10) if intx.get_lane(f"{d}-{i}"))
                        if not has_main_traffic:
                            can_pass = True
                        elif lane.get_max_waiting_time(current_time) > 30: # Even secondary roads move eventually
                            can_pass = True

                if can_pass:
                    lane.remove_vehicle()

    def run_tick(self):
        # 1. Update Traffic Lights Timer (only if signalized or RL)
        if self.current_rule in ["SIGNALIZED", "RL_TRAINED"]:
            raw_data = self.input_handler.get_traffic_data()
            analyzed_data = self.traffic_analyzer.analyze(raw_data)
            
            if self.current_rule == "SIGNALIZED":
                decisions = self.inference_engine.infer_next_states(analyzed_data, {})
            else: # RL_TRAINED
                decisions = self.rl_agent.infer_next_states(analyzed_data, self)
                
            self.scheduler.execute_decisions(decisions, analyzed_data)
            
            # Apply manual overrides if any
            for int_id, lanes in self.overrides.items():
                intx = next((i for i in self.intersections if i.id == int_id), None)
                if intx:
                    for lane_id, state in lanes.items():
                        sig = intx.get_signal(lane_id)
                        if sig:
                            sig.set_state(state, 99) # Set a high timer so it doesn't expire immediately

        # 2. Generate Random Traffic
        self.traffic_generator.generate_random_traffic()

        # 3. Process passing vehicles
        self.process_vehicles()
        
        # 4. Advance Time
        self.timer.tick(1)
        
    def simulate(self, ticks):
        for _ in range(ticks):
            self.run_tick()
            time.sleep(0.1)

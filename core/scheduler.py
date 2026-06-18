from utils.constants import Constants

class Scheduler:
    def __init__(self, environment, signal_controller):
        self.environment = environment
        self.signal_controller = signal_controller
        self.lane_order = ["North", "East", "South", "West"]

    def execute_decisions(self, decisions, traffic_data):
        for intersection in self.environment.intersections:
            decision = decisions.get(intersection.id)
            if not decision:
                continue

            active_direction = intersection.active_lane
            active_signal = None
            if active_direction:
                for sig in intersection.get_all_signals():
                    if sig.lane_name.startswith(active_direction):
                        active_signal = sig
                        break
            
            # --- TRANSITION LOGIC (YELLOW PHASE) ---
            if active_signal and active_signal.state == Constants.YELLOW:
                if active_signal.timer > 0:
                    continue
                else:
                    self.signal_controller.set_all_red(intersection)
                    intersection.all_red_timer = Constants.ALL_RED_DURATION
                    print(f"[SAFETY] {intersection.id}: All-red clearance active.")
                    continue # Wait for next tick to pick next lane

            # If current is green and has time, continue
            if active_signal and active_signal.state == Constants.GREEN and active_signal.timer > 0 and decision["type"] != "emergency":
                continue

            # Safety check: Block while all-red timer is active
            if hasattr(intersection, 'all_red_timer') and intersection.all_red_timer > 0:
                if decision["type"] != "emergency": 
                    continue

            # --- SWITCHING LOGIC ---
            target_direction = None
            duration = 0

            def get_dir(target):
                return target.split('-')[0] if target and '-' in target else target

            if decision["type"] == "emergency":
                target_direction = get_dir(decision["target_lane"])
                duration = 30 
                if active_direction and active_direction != target_direction:
                    print(f"[EMERGENCY] Instant override at {intersection.id} for {target_direction}")
            elif decision["type"] == "force_switch":
                target_direction = self._get_next_lane(active_direction)
                rep_lane = f"{target_direction}-1"
                vehicle_count = traffic_data[intersection.id].get(rep_lane, {'count': 0})['count']
                duration = self.signal_controller.calculate_green_time(vehicle_count)
            elif decision["type"] == "greedy":
                target_direction = get_dir(decision["target_lane"])
                rep_lane = decision["target_lane"]
                vehicle_count = traffic_data[intersection.id].get(rep_lane, {'count': 0})['count']
                duration = self.signal_controller.calculate_green_time(vehicle_count, factor=3)
            elif decision["type"] == "fast_cycle":
                target_direction = self._get_next_lane(active_direction)
                duration = self.signal_controller.base_green_time * Constants.NO_TRAFFIC_CYCLE_REDUCTION
            else:
                target_direction = self._get_next_lane(active_direction)
                rep_lane = f"{target_direction}-1"
                vehicle_count = traffic_data[intersection.id].get(rep_lane, {'count': 0})['count']
                duration = self.signal_controller.calculate_green_time(vehicle_count)

            # Apply switch
            if target_direction and target_direction != active_direction:
                if active_signal and active_signal.state == Constants.GREEN and decision["type"] != "emergency":
                    print(f"[TRANSITION] {intersection.id}: {active_direction} turning YELLOW.")
                    self.signal_controller.set_yellow(intersection, active_direction, Constants.YELLOW_DURATION)
                else:
                    print(f"[SWITCH] {intersection.id}: {target_direction} turning GREEN for {duration}s.")
                    self.signal_controller.set_signal(intersection, target_direction, duration)
            elif active_signal and active_signal.timer == 0 and active_signal.state == Constants.GREEN:
                 self.signal_controller.set_signal(intersection, target_direction, duration)

    def _get_next_lane(self, current_lane_name):
        if not current_lane_name:
            return self.lane_order[0]
        try:
            idx = self.lane_order.index(current_lane_name)
            return self.lane_order[(idx + 1) % len(self.lane_order)]
        except ValueError:
            return self.lane_order[0]

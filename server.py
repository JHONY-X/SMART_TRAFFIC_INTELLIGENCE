import os
import sys
from flask import Flask, jsonify, request, send_from_directory
from simulation.environment import Environment

app = Flask(__name__, static_folder='web')

# Global environment instance
env = None

def init_env():
    global env
    env = Environment("data/config.json", "data/rules.json")

@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def send_assets(path):
    return send_from_directory('web', path)

@app.route('/api/state', methods=['GET'])
def get_state():
    if env is None:
        init_env()
    
    state = {
        "time": env.timer.get_time(),
        "rule": env.current_rule,
        "intersections": []
    }
    
    for intx in env.intersections:
        intx_data = {
            "id": intx.id,
            "lanes": []
        }
        for name, signal in intx.signals.items():
            lane = intx.get_lane(name)
            intx_data["lanes"].append({
                "name": name,
                "signal_state": signal.state,
                "signal_timer": signal.timer,
                "vehicle_count": lane.get_vehicle_count(),
                "vehicles": [v.id for v in lane.vehicles],
                "has_emergency": lane.has_emergency_vehicle()
            })
        state["intersections"].append(intx_data)
    
    return jsonify(state)

@app.route('/api/config', methods=['POST'])
def update_config():
    if env is None:
        init_env()
    
    data = request.json
    if "rule" in data:
        env.set_rule(data["rule"])
    
    if "main_lanes" in data and "secondary_lanes" in data:
        env.reconfigure_lanes(data["main_lanes"], data["secondary_lanes"])
        
    return get_state()

@app.route('/api/traffic', methods=['POST'])
def update_traffic():
    if env is None:
        init_env()
    
    data = request.json
    if "intensity" in data:
        env.traffic_generator.set_intensity(data["intensity"])
        
    return get_state()

@app.route('/api/tick', methods=['POST'])
def tick():
    if env is None:
        init_env()
    
    steps = request.json.get('steps', 1) if request.is_json else 1
    for _ in range(steps):
        env.run_tick()
    
    return get_state()

@app.route('/api/reset', methods=['POST'])
def reset():
    init_env()
    return get_state()

@app.route('/api/signal/override', methods=['POST'])
def override_signal():
    if env is None:
        init_env()
    
    data = request.json
    int_id = data.get("intersection_id")
    lane_id = data.get("lane_id")
    state = data.get("state") # "RED", "YELLOW", "GREEN" or None to clear
    
    if int_id:
        if int_id not in env.overrides:
            env.overrides[int_id] = {}
        
        if state:
            env.overrides[int_id][lane_id] = state
        else:
            if lane_id in env.overrides[int_id]:
                del env.overrides[int_id][lane_id]
            if not env.overrides[int_id]:
                del env.overrides[int_id]
                
    return get_state()

@app.route('/api/test_case/<int:case_id>', methods=['POST'])
def run_test_case(case_id):
    if env is None:
        init_env()
    
    if case_id == 1:
        env.traffic_generator.simulate_test_case_1("INT-1", "North")
    elif case_id == 2:
        init_env()
    elif case_id == 3:
        env.traffic_generator.simulate_test_case_3("INT-1", "West")
    elif case_id == 4:
        env.traffic_generator.simulate_test_case_1("INT-1", "East")
        env.traffic_generator.simulate_test_case_1("INT-2", "East")
    
    return get_state()

if __name__ == '__main__':
    init_env()
    app.run(host='0.0.0.0', port=9090, debug=True)










import requests
import json
import time

URL = "http://localhost:9090"

def get_state():
    return requests.get(f"{URL}/api/state").json()

def post_config(rule):
    return requests.post(f"{URL}/api/config", json={"rule": rule}).json()

def post_traffic(intensity):
    return requests.post(f"{URL}/api/traffic", json={"intensity": intensity}).json()

def post_tick(steps=1):
    return requests.post(f"{URL}/api/tick", json={"steps": steps}).json()

print("Initial State:")
state = get_state()
print(f"Rule: {state['rule']}")

print("\nSwitching to RIGHT_PRIORITY...")
state = post_config("RIGHT_PRIORITY")
print(f"Rule: {state['rule']}")

print("\nIncreasing traffic intensity to 90...")
state = post_traffic(90)
# We don't see immediate vehicle changes until ticks happen

print("\nTicking 5 times...")
state = post_tick(5)
total_vehicles = sum([len(lane['vehicles']) for intx in state['intersections'] for lane in intx['lanes']])
print(f"Total Vehicles after ticks: {total_vehicles}")

print("\nSwitching back to SIGNALIZED...")
state = post_config("SIGNALIZED")
print(f"Rule: {state['rule']}")


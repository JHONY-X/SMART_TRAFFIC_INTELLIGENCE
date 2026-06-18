import sys
import os
import random
from simulation.environment import Environment
from modules.rl_agent import RLAgent

def train(epochs=100, steps_per_epoch=200):
    print("Initializing training environment...")
    env = Environment("data/config.json", "data/rules.json")
    agent = RLAgent("data/q_table.json")
    
    alpha = 0.2
    gamma = 0.9
    epsilon = 0.5
    min_epsilon = 0.05
    decay = 0.95
    
    print(f"Starting Q-Learning training for {epochs} epochs ({steps_per_epoch} steps each)...")
    
    for epoch in range(epochs):
        # Reset environment
        env.timer.time = 0
        for intersection in env.intersections:
            for lane in intersection.get_all_lanes():
                lane.vehicles = []
            intersection.active_lane = None
            intersection.all_red_timer = 0
            
        # Run epoch
        epoch_reward = 0
        total_vehicles = 0
        
        # We make decisions every 5 ticks (5 seconds)
        decision_interval = 5
        
        # Initial state
        raw_data = env.input_handler.get_traffic_data()
        state = agent.get_state(raw_data, "INT-1")
        
        for step in range(steps_per_epoch):
            # Generate new vehicles
            env.traffic_generator.generate_random_traffic(emergency_prob=0.02)
            
            # If it's a decision tick
            if step % decision_interval == 0:
                action_idx = agent.choose_action(state, epsilon)
                chosen_dir = agent.actions[action_idx]
                
                # Apply action (directly control signal green light)
                intersection = env.intersections[0] # assuming single intersection INT-1
                active_dir_before = intersection.active_lane
                
                # Use signal controller to set green light for chosen direction
                env.signal_controller.set_signal(intersection, chosen_dir, duration=decision_interval)
                
            # Run one step of vehicle passing and tick timer
            env.process_vehicles()
            env.timer.tick(1)
            
            # Post-tick update
            if step % decision_interval == 0:
                # Observe next state and calculate reward
                next_raw_data = env.input_handler.get_traffic_data()
                next_state = agent.get_state(next_raw_data, "INT-1")
                
                # Calculate reward: negative of vehicle count
                vehicle_count = sum(l['count'] for l in next_raw_data["INT-1"].values())
                reward = -vehicle_count
                
                # Penalize emergency vehicle waiting
                has_emergency = any(l['has_emergency'] for l in next_raw_data["INT-1"].values())
                if has_emergency:
                    # check if the chosen direction has the emergency vehicle
                    emergencies_in_chosen = False
                    for lane_name, metrics in next_raw_data["INT-1"].items():
                        if lane_name.startswith(chosen_dir) and metrics['has_emergency']:
                            emergencies_in_chosen = True
                    if not emergencies_in_chosen:
                        reward -= 50 # heavy penalty for blocking emergency vehicles
                
                # Small penalty for switching signal states to prevent oscillation
                if active_dir_before and active_dir_before != chosen_dir:
                    reward -= 2
                    
                # Update Q-table
                agent.update(state, action_idx, reward, next_state, alpha, gamma)
                
                state = next_state
                epoch_reward += reward
                total_vehicles += vehicle_count
                
        # Decay exploration rate
        epsilon = max(min_epsilon, epsilon * decay)
        
        if (epoch + 1) % 10 == 0 or epoch == 0:
            avg_reward = epoch_reward / (steps_per_epoch / decision_interval)
            avg_vehicles = total_vehicles / steps_per_epoch
            print(f"Epoch {epoch+1:02d}/{epochs} | Epsilon: {epsilon:.3f} | Avg Reward: {avg_reward:.2f} | Avg Queue: {avg_vehicles:.2f}")
            
    # Save the trained table
    agent.save_q_table()
    print("Training finished! Q-Table saved successfully to 'data/q_table.json'.")

if __name__ == "__main__":
    epochs = 100
    if len(sys.argv) > 1:
        epochs = int(sys.argv[1])
    train(epochs=epochs)

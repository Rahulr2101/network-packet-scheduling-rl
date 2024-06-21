import gym
import simpy_env

# Create an instance of the environment
env = gym.make('SimPyEnv-v0')

# Reset the environment to the initial state
obs = env.reset()

# Run the environment with random actions for 1000 steps
for _ in range(1000):
    action = env.action_space.sample()  # Sample a random action
    obs, reward, done, info = env.step(action)
    print(f"Action: {action}, Observation: {obs}, Reward: {reward}, Done: {done}")
    if done:
        break
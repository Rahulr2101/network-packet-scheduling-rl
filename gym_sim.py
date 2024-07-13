import gym
import simpy_env

def run():
    env = gym.make('SimPyEnv-v0',testing=True)
    state, reward, done, info = env.reset()  # Properly reset and get initial state
    while not done:

        if state[0] != 0:
            action = 2  # Move packets from sw1 to destination
            state, reward, done, info = env.step(action)
        if state[1] != 0:
            action = 3  # Move packets from sw2 to destination
            state, reward, done, info = env.step(action)
        else:
            action = 4  # Do nothing if both switches are empty
            state, reward, done, info = env.step(action)

if __name__ == "__main__":
    run()

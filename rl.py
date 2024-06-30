import gym
import simpy_env
import numpy as np
import pickle
import matplotlib.pyplot as plt
import tabulate

def run(episode,is_training=True):
    env = gym.make('SimPyEnv-v0')

    if(is_training):
        q = np.zeros((400,400,5))
    else:
        f=open("nw.pkl","r")
        episode =1
        with open('nw.pkl', 'rb') as f:
            q = pickle.load(f)
    learning_rate = 0.1
    discount_factor = 0.99
    epsilon = 1
    epsilon_decay = 0.00005
    rng = np.random.default_rng()
    rewards_per_episode = np.zeros(episode)
  

    for i in range(episode):
        state,reward,done,info = env.reset()
        episode_reward = 0
        while not done:
            if is_training and rng.random() <epsilon:
                action = env.action_space.sample()
            else:
                action = np.argmax(q[state[0],state[1],:])
            next_state, reward, done, info = env.step(action)
            episode_reward += reward

            if is_training:
                 
                 q[state[0],state[1],action] = q[state[0],state[1],action] + learning_rate * (
                    reward + discount_factor * np.max(q[next_state[0],next_state[1],:]) - q[state[0],state[1],action]
                )
            state = next_state
        epsilon = max(epsilon - epsilon_decay, 0)
        if(epsilon==0):
            learning_rate = 0.001
        if i % 100 == 0:
                print(f"Episode {i} Reward {episode_reward} Epsilon {epsilon}")

            
        rewards_per_episode[i] = episode_reward
    
    sum_rewards = np.zeros(episode)
    for t in range(episode):
        sum_rewards[t] = np.sum(rewards_per_episode[max(0, t - 100):(t + 1)])

    plt.plot(sum_rewards, label="Rewards per Episode")
    plt.xlabel("Episode")
    plt.ylabel("Total Reward")
    plt.title("Rewards Collected per Episode")
    plt.legend()

    if is_training:
        plt.savefig('nw_environment.png')
        with open("nw.pkl", "wb") as f:
            pickle.dump(q, f)


if __name__ == "__main__":
    run(episode=20000, is_training=False)
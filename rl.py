import gym
import simpy_env
import numpy as np
import pickle
import matplotlib.pyplot as plt
import tabulate

def run(episode,is_training=True):
    if is_training:
        env = gym.make('SimPyEnv-v0')
    else:
        env = gym.make('SimPyEnv-v0', testing=True) 

    if(is_training):
        q1 = np.zeros((151,151,5))
        q2 = np.zeros((151,151,5))
    else:
        f=open("nw.pkl","r")
        episode =1
        with open('nw_q1.pkl', 'rb') as f1,open('nw_q2.pkl','rb') as f2:
            q1 = pickle.load(f1)
            q2 = pickle.load(f2)
    learning_rate = 0.0001
    discount_factor = 0.99
    epsilon = 1
    epsilon_decay = 0.0001
    rng = np.random.default_rng()
    rewards_per_episode = np.zeros(episode)
  


    for i in range(episode):
        state,reward,done,info = env.reset()
        episode_reward = 0
        while not done:
            if is_training and rng.random() <epsilon:
                action = env.action_space.sample()
            else:
                 action = np.argmax(q1[state[0], state[1], :] + q2[state[0], state[1], :])
            next_state, reward, done, info = env.step(action)
            episode_reward += reward

            if is_training:
                if rng.random() < 0.5:
                    best_action = np.argmax(q1[next_state[0],next_state[1],:])
                    q1[state[0], state[1], action] = q1[state[0], state[1], action] + learning_rate * (
                        reward + discount_factor * q2[next_state[0], next_state[1], best_action] - q1[state[0], state[1], action]
                    )
                else:
                    best_action = np.argmax(q2[next_state[0], next_state[1], :])
                    q2[state[0], state[1], action] = q2[state[0], state[1], action] + learning_rate * (
                        reward + discount_factor * q1[next_state[0], next_state[1], best_action] - q2[state[0], state[1], action]
                    )
            state = next_state
        if epsilon > 0.05:
            epsilon -= epsilon_decay
        else:
            epsilon = 0.05
        # if(epsilon==0):
        #     learning_rate = 0.001
        
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
        with open("nw_q1.pkl", "wb") as f1, open("nw_q2.pkl", "wb") as f2:
            pickle.dump(q1, f1)
            pickle.dump(q2, f2)


if __name__ == "__main__":
    run(episode=20000, is_training=False)
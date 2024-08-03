import gym
import simpy_env
import numpy as np
from collections import deque
import matplotlib.pyplot as plt
import random
import torch
from torch import nn
import torch.nn.functional as F

# Set the device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

class DQN(nn.Module):
    def __init__(self, in_states, h1_nodes, out_actions):
        super().__init__()
        self.fc1 = nn.Linear(in_states, h1_nodes)
        self.out = nn.Linear(h1_nodes, out_actions)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.out(x)
        return x

class ReplayMemory():
    def __init__(self, maxLen):
        self.memory = deque([], maxlen=maxLen)
    def append(self, transition):
        self.memory.append(transition)
    def sample(self, sample_size):
        return random.sample(self.memory, sample_size)
    def __len__(self):
        return len(self.memory)

class DQNetwork():
    learning_rate_a = 0.001
    discount_factor_g = 0.9
    network_sync_rate = 10
    replay_memory_size = 50000
    mini_batch_size = 32

    loss_fn = nn.MSELoss()
    optimizer = None

    def train(self, episodes):
        env = gym.make('SimPyEnv-v0')
        num_states = 22500
        num_actions = 4

        epsilon = 1
        memory = ReplayMemory(self.replay_memory_size)
        policy_dqn = DQN(in_states=num_states, h1_nodes=1000, out_actions=num_actions).to(device)
        target_dqn = DQN(in_states=num_states, h1_nodes=1000, out_actions=num_actions).to(device)
        target_dqn.load_state_dict(policy_dqn.state_dict())
        self.optimizer = torch.optim.Adam(policy_dqn.parameters(), lr=self.learning_rate_a)
        rewards_per_episode = np.zeros(episodes)
        epsilon_history = []

        step_count = 0

        for i in range(episodes):
            state, reward, done, truncated, info = env.reset()

            while(not done and not truncated):
                if random.random() < epsilon:
                    action = env.action_space.sample()
                else:
                    with torch.no_grad():
                        action = policy_dqn(self.state_to_dqn_input(state, num_states)).argmax().item()

                new_state, reward, done, truncated, info = env.step(action)
                memory.append((state, action, new_state, reward, done, info))

                state = new_state
                rewards_per_episode[i] = reward
            if i%100==0:
                print(f"Episode {i} Epsilon {epsilon}")

            if len(memory) > self.mini_batch_size:
                mini_batch = memory.sample(self.mini_batch_size)
                self.optimize(mini_batch, policy_dqn, target_dqn)        

                # Decay epsilon
                epsilon = max(epsilon - 1/episodes, 0)
                epsilon_history.append(epsilon)

                # Copy policy network to target network after a certain number of steps
                if step_count > self.network_sync_rate:
                    target_dqn.load_state_dict(policy_dqn.state_dict())
                    step_count = 0

        torch.save(policy_dqn.state_dict(), "dql.pt")

        plt.figure(1)
        sum_rewards = np.zeros(episodes)
        for x in range(episodes):
            sum_rewards[x] = np.sum(rewards_per_episode[max(0, x-100):(x+1)])
        plt.subplot(121)  # plot on a 1 row x 2 col grid, at cell 1
        plt.plot(sum_rewards)
        
        # Plot epsilon decay (Y-axis) vs episodes (X-axis)
        plt.subplot(122)  # plot on a 1 row x 2 col grid, at cell 2
        plt.plot(epsilon_history)
        plt.savefig('dql.png')

    def optimize(self, mini_batch, policy_dqn, target_dqn):
    # Get number of input nodes
        num_states = policy_dqn.fc1.in_features

        current_q_list = []
        target_q_list = []

        for state, action, new_state, reward, done, info in mini_batch:
            if done: 
                target = torch.tensor([reward], dtype=torch.float32, device=device)
            else:
                with torch.no_grad():
                    target = reward + self.discount_factor_g * target_dqn(self.state_to_dqn_input(new_state, num_states)).max()
                    target = torch.tensor([target], dtype=torch.float32, device=device)

            current_q = policy_dqn(self.state_to_dqn_input(state, num_states))
            current_q_list.append(current_q)

            target_q = target_dqn(self.state_to_dqn_input(state, num_states)) 
            target_q[action] = target
            target_q_list.append(target_q)
                
        loss = self.loss_fn(torch.stack(current_q_list), torch.stack(target_q_list))

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()



    def state_to_dqn_input(self, state: int, num_states: int) -> torch.Tensor:
        input_tensor = torch.zeros(num_states, device=device)
        input_tensor[state] = 1
        return input_tensor

    def test(self, episodes):
        env = gym.make('SimPyEnv-v0', testing=True)
        num_states = 22500
        num_actions = 4

        policy_dqn = DQN(in_states=num_states, h1_nodes=num_states, out_actions=num_actions).to(device)
        policy_dqn.load_state_dict(torch.load("dql.pt", map_location=device))
        policy_dqn.eval()

        for i in range(episodes):
            state = env.reset()[0]
            terminated = False
            truncated = False

            while(not terminated and not truncated):  
                with torch.no_grad():
                    action = policy_dqn(self.state_to_dqn_input(state, num_states)).argmax().item()

                state, reward, terminated, truncated, _ = env.step(action)

if __name__ == '__main__':
    network = DQNetwork()
    network.train(10000)
    network.test(1)
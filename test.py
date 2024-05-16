import numpy as np

# Define the number of states and actions
num_states = 91
num_actions = 4

# Create a NumPy array to store state-action information
state_action_space = np.empty((num_states, 3), dtype=object)

# Fill the state information with [q1, q2] values
for i in range(num_states):
    state_action_space[i, 0] = f"q{i+1}"  # State

# Add a column for possible actions
state_action_space[:, 1:] = ['a1', 'a2', 'a3', 'a4']

# Print the state-action space
print(state_action_space)

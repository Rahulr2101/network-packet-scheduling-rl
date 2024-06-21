import gym
from gym import spaces
import numpy as np
import simpy

class Packet():
    def __init__(self, id, src, dst, timestamp, packet_size):
        self.id = id
        self.src = src
        self.dst = dst
        self.timestamp = timestamp
        self.packet_size = packet_size



class SimPyEnv(gym.Env):
    def __init__(self):
        super(SimPyEnv, self).__init__()
        self.max_capacity = 150
        self.env = simpy.Environment()
        self.es1 = simpy.Store(self.env, capacity=self.max_capacity)
        self.es2 = simpy.Store(self.env, capacity=self.max_capacity)
        self.es3 = simpy.Store(self.env, capacity=20000)
        self.sw1 = simpy.Store(self.env, capacity=self.max_capacity)
        self.sw2 = simpy.Store(self.env, capacity=self.max_capacity)
        self.actions_step = {0: "sw1_to_sw2", 1: "sw2_to_sw1", 2: "sw1_to_dest", 3: "sw2_to_dest"}
        self.link_speeds = {"sw1": {"es1": 600, "dest": 100, "sw2": 800}, "sw2": {"es2": 800, "dest": 800, "sw1": 900}}
        self.logs_list = []
        self.action_space = spaces.Discrete(5)
        self.observation_space = spaces.Box(low=0, high=self.max_capacity, shape=(2,), dtype=np.float32)
        self.reward_range = (-1, 1)
        self.current_time = 0
        self.done = False
        self.info = {}
        self.state = [0, 0]
        self.reward = 0

    def reset(self):
        self.env = simpy.Environment()
        self.es1 = simpy.Store(self.env, capacity=self.max_capacity)
        self.es2 = simpy.Store(self.env, capacity=self.max_capacity)
        self.es3 = simpy.Store(self.env, capacity=20000)
        self.sw1 = simpy.Store(self.env, capacity=self.max_capacity)
        self.sw2 = simpy.Store(self.env, capacity=self.max_capacity)
        self.state = [0, 0]
        self.done = False
        self.current_time = 0
        self.reward = 0

        # Generate packets
        self.env.process(self.packet_generator("es1", "sw1", self.es1, 64))
        self.env.process(self.packet_generator("es2", "sw2", self.es2, 64))

        # Define the SimPy processes for the switches
        self.env.process(self.switch(self.es1, self.sw1, self.link_speeds["sw1"]["es1"]))
        self.env.process(self.switch(self.es2, self.sw2, self.link_speeds["sw2"]["es2"]))

        return np.array(self.state, dtype=np.float32)
    
    def packet_generator(self, src, dst, host, packet_size, packet_number=50):
        batch =3
        delay = 3
       
        for i in range(batch):
            yield self.env.timeout(delay)
            for j in range(50):
                packet = Packet(id=j, src=src, dst=dst, timestamp=self.env.now, packet_size=packet_size)
                yield host.put(packet)

    def step(self, action):
        # Define a SimPy process for the selected action
        if action == 0:
            self.env.process(self.sender(self.sw1, self.sw2, self.link_speeds["sw1"]["sw2"]))
        elif action == 1:
            self.env.process(self.sender(self.sw2, self.sw1, self.link_speeds["sw2"]["sw1"]))
        elif action == 2:
            self.env.process(self.sender(self.sw1, self.es3, self.link_speeds["sw1"]["dest"]))
        elif action == 3:
            self.env.process(self.sender(self.sw2, self.es3, self.link_speeds["sw2"]["dest"]))
        elif action == 4:
            pass

        # Run the SimPy environment for one time step
        self.env.run(until=self.current_time + 1)
        self.current_time += 1

        # Update the state
        self.state = [len(self.sw1.items), len(self.sw2.items)]

        # Define a simple reward
        reward = 1.0 if len(self.es3.items) > 0 else -0.1

        # Check if the episode is done
        self.done = len(self.es3.items) == 300
        print(len(self.es3.items)) # Example: end after 10 time steps

        return np.array(self.state, dtype=np.float32), reward, self.done, self.info

    def sender(self, src, dst, link_speed):
      
        packet = yield src.get()
        transmission_delay = packet.packet_size / link_speed
        yield self.env.timeout(transmission_delay)
        yield dst.put(packet)

    def switch(self, es, sw, speed):
        while True:
            packet = yield es.get()
            transmission_delay = packet.packet_size / speed
            yield self.env.timeout(transmission_delay)
            yield sw.put(packet)

# Register the custom environment with Gym
from gym.envs.registration import register

register(
    id='SimPyEnv-v0',
    entry_point='simpy_env:SimPyEnv',
)
       

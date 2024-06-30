import gym
from gym import spaces
import numpy as np
import simpy
import tabulate

class Packet():
    def __init__(self, id, src, dst, timestamp, packet_size):
        self.id = id
        self.src = src
        self.dst = dst
        self.processed = False
        self.timestamp = timestamp
        self.packet_size = packet_size
    def __lt__(self, other):
        return self.timestamp < other.timestamp

class SimPyEnv(gym.Env):
    def __init__(self):
        super(SimPyEnv, self).__init__()
        self.max_capacity = 150
        self.testing = True
        self.env = simpy.Environment()
        self.es1 = simpy.Store(self.env, capacity=self.max_capacity)
        self.es2 = simpy.Store(self.env, capacity=self.max_capacity)
        self.es3 = simpy.Store(self.env, capacity=20000)
        self.sw1 = simpy.PriorityStore(self.env, capacity=self.max_capacity)
        self.sw2 = simpy.PriorityStore(self.env, capacity=self.max_capacity)
        self.actions_step = {0: "sw1_to_sw2", 1: "sw2_to_sw1", 2: "sw1_to_dest", 3: "sw2_to_dest"}
        self.link_speeds = {"sw1": {"es1": 1000, "dest": 900, "sw2": 900}, "sw2": {"es2": 800, "dest": 1000, "sw1": 900}}
        self.logs_list = []
        self.action_space = spaces.Discrete(5)
        self.observation_space = spaces.Box(low=0, high=self.max_capacity, shape=(2,), dtype=np.float32)
        self.reward_range = (-1, 1)
        self.current_time = 0
        self.count = 0
        self.done = False
        self.info = []
        self.state = [0, 0]
        self.old_state = self.state
        self.reward = 0
        self.delay_multiplier = 10000

    def reset(self):
        self.env = simpy.Environment()
        self.es1 = simpy.Store(self.env, capacity=self.max_capacity)
        self.es2 = simpy.Store(self.env, capacity=self.max_capacity)
        self.es3 = simpy.Store(self.env, capacity=20000)
        self.sw1 = simpy.PriorityStore(self.env, capacity=self.max_capacity)
        self.sw2 = simpy.PriorityStore(self.env, capacity=self.max_capacity)
        self.state = [0, 0]
        self.timestamps = []
        self.old_state = self.state
        self.done = False
        self.current_time = 0
        self.reward = 0

        # Generate packets
        if not self.testing:
            self.rand1 = np.random.randint(70, 100)
            self.rand2 = np.random.randint(30, 60)
        else:
            self.rand1 = 100
            self.rand2 = 60
        self.total_packets = (self.rand1 + self.rand2) * 3
        self.env.process(self.packet_generator("es1", "sw1", self.es1, 0.064, delay=30, packet_number=self.rand1))
        self.env.process(self.packet_generator("es2", "sw2", self.es2, 0.064, delay=30, packet_number=self.rand2))
        self.count = 0

        # Define the SimPy processes for the switches
        self.env.process(self.switch(self.es1, self.sw1, self.link_speeds["sw1"]["es1"]))
        self.env.process(self.switch(self.es2, self.sw2, self.link_speeds["sw2"]["es2"]))

        return np.array(self.state, dtype=np.int64), self.reward, self.done, self.info

    def packet_generator(self, src, dst, host, packet_size, delay=60, packet_number=50):
        batch = 3
        for i in range(batch):
            for j in range(packet_number):
                packet = Packet(id=j, src=src, dst=dst, timestamp=self.env.now, packet_size=packet_size)
                yield host.put(packet)
            yield self.env.timeout(delay)

    def step(self, action):
        # Define a SimPy process for the selected action
        reward = 0
        if action == 0:
            self.env.process(self.sender(self.sw1, self.sw2, "sw1", "sw2", self.link_speeds["sw1"]["sw2"]))
        elif action == 1:
            self.env.process(self.sender(self.sw2, self.sw1, "sw2", "sw1", self.link_speeds["sw2"]["sw1"]))
        elif action == 2:
            if len(self.sw1.items) > 0:
                reward += 5
            else:
                reward -= 10
            self.env.process(self.sender(self.sw1, self.es3, "sw1", "es3", self.link_speeds["sw1"]["dest"]))
        elif action == 3:
            if len(self.sw2.items) > 0:
                reward += 5
            else:
                reward -= 10
            self.env.process(self.sender(self.sw2, self.es3, "sw2", "es3", self.link_speeds["sw2"]["dest"]))
        elif action == 4:
            if len(self.sw1.items) + len(self.sw2.items) > 0:
                reward -= 20
            pass
        # Run the SimPy environment for a larger time step to balance performance and accuracy
        self.env.run(until=self.env.now + 3)
        self.state = [len(self.sw1.items), len(self.sw2.items)]
        if action != 4:
            for packet in list(self.es3.items):
                if not packet.processed:
                    packet.processed = True
                    self.timestamps.append(self.env.now - packet.timestamp)
                    if self.env.now - packet.timestamp <= 45:
                        reward += 1
                        continue
                    else:
                        if self.testing:
                            self.count += 1
        self.done = len(self.es3.items) == self.total_packets or self.env.now > 1400

        if self.done:
            if len(self.es3.items) != self.total_packets:
                remaining = self.total_packets - len(self.es3.items)
                reward -= remaining * 0.1
            else:
                reward += 100
            if self.testing:
                self.display()
                remaining = self.total_packets - len(self.es3.items)
                loss = int(((self.count + remaining) / self.total_packets) * 100)
                print(f"Completed in {self.env.now} ms Total Packet = {self.total_packets}  Packets drop = {loss}%")

        return np.array(self.state, dtype=np.int64), reward, self.done, {}

    def display(self):
        print(tabulate.tabulate(self.info, headers=["Packet ID", "Action", "Delay(in Sec)", "Packet Time", "Current_time(in Sec)", "Switch 1 Queue Length", "Switch 2 Queue Length"]))

    def sender(self, src, dst, n1, n2, link_speed):
        packet = yield src.get()
        transmission_delay = (packet.packet_size / link_speed) * self.delay_multiplier
        yield self.env.timeout(transmission_delay)
        yield dst.put(packet)
        if self.testing:
            self.info.append([packet.id, n1 + " to " + n2, transmission_delay, self.env.now - packet.timestamp,
                              self.env.now, len(self.sw1.items), len(self.sw2.items)])

    def switch(self, es, sw, speed):
        while True:
            packet = yield es.get()
            transmission_delay = (packet.packet_size / speed) * self.delay_multiplier
            yield self.env.timeout(transmission_delay)
            yield sw.put(packet)

# Register the custom environment with Gym
from gym.envs.registration import register

register(
    id='SimPyEnv-v0',
    entry_point='simpy_env:SimPyEnv',
)

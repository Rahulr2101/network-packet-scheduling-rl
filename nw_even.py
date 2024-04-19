import simpy


packet_size = 1000


class Packet:
    def __init__(self, id, src, dst):
        self.id = id
        self.src = src
        self.dst = dst





class NetworkEnvironment:
    """
    Represents the network environment for reinforcement learning.
    """

    def __init__(self, time,capacity=10, link_speeds=[1000, 300, 400, 800, 200]):
        self.env = simpy.Environment()
        self.es1 = simpy.Store(self.env, capacity=capacity)
        self.es2 = simpy.Store(self.env, capacity=capacity)
        self.es3 = simpy.Store(self.env, capacity=capacity)
        self.sw1 = simpy.Store(self.env, capacity=capacity)
        self.sw2 = simpy.Store(self.env, capacity=capacity)
        self.link_speeds = link_speeds

        self.create_environment(time)
          # Call the environment setup function


    def switch(self,env, es, speed):
        """
        Simulates packet switching behavior.
        """
        while True:
            packet = yield es.get()
            transmission_delay = packet_size / speed
            print(f"Transmitting packet{packet.id} from {packet.src} to {packet.dst} - Delay: {transmission_delay:.4f} seconds  - Current time:{env.now} seconds - Current Switch 1 Queue Length: {len(self.sw1.items)}') - Current Switch 2 Queue Length: {len(self.sw2.items)} ")
            packet.src = packet.dst
            yield env.timeout(transmission_delay)
            if packet.dst == "switch1":
                yield self.sw1.put(packet)
            else:
                yield self.sw2.put(packet)

    def send_packet_to_es3(self, env, es, sw, speed):
        """
        Sends packets received by the switch to es3.
        """
        while True:
            packet = yield sw.get()
            transmission_delay = packet_size / speed
            print(f"Transmitting packet{packet.id} from {packet.src} to es3 - Delay: {transmission_delay:.4f} seconds - Current time:{env.now} seconds")
            yield env.timeout(transmission_delay)
            yield es.put(packet)

    def packet_generator(self, env, src, dst, host):
        """
        Generates packets with increasing IDs at a specified interval.
        """
        packet_id = 1
        while True:
            packet = Packet(packet_id, src, dst)
            yield host.put(packet)
            packet_id += 1

    def create_environment(self,time):
        """
        Sets up the network environment with processes.
        """
        host_process1 = self.env.process(self.packet_generator(self.env, "es1", "switch1", self.es1))
        host_process2 = self.env.process(self.packet_generator(self.env, "es2", "switch2", self.es2))
        switch_process1 = self.env.process(self.switch(self.env, self.es1, self.link_speeds[0]))
        self.env.process(self.send_packet_to_es3(self.env, self.es3,self.sw1,self.link_speeds[1]))
        switch_process2 = self.env.process(self.switch(self.env,self.es2,self.link_speeds[2]))
        self.env.process(self.send_packet_to_es3(self.env,self.es3,self.sw2,self.link_speeds[4]))
        self.env.run(until=time)
import simpy


packet_size = 1000

class Packet:
    def __init__(self, id, current,src,dst):
        self.id = id
        self.src = src
        self.currrent = current
        self.dst = dst

class NetworkEnvironment:
    def __init__(self, time,capacity=10, link_speeds={"sw1":{"es1":1000,"dest":1,"sw2":800}, "sw2":{"es2":400,"dest":1,"sw1":800}}):
        self.env = simpy.Environment()
        self.es1 = simpy.Store(self.env, capacity=capacity)
        self.es2 = simpy.Store(self.env, capacity=capacity)
        self.es3 = simpy.Store(self.env, capacity=capacity)
        self.sw1 = simpy.Store(self.env, capacity=capacity)
        self.sw2 = simpy.Store(self.env, capacity=capacity)
        self.link_speeds = link_speeds

        self.create_environment(time)
          # Call the environment setup function


    def switch(self,env, es,sw,speed):
        """
        Simulates packet switching behavior.
        """
        while True:
            packet = yield es.get()
            transmission_delay = packet_size / speed
            print(f"Transmitting packet{packet.id} from {packet.src} to {packet.dst} - Delay: {transmission_delay:.4f} seconds  - Current time:{env.now} seconds - Current Switch 1 Queue Length: {len(self.sw1.items)}' - Current Switch 2 Queue Length: {len(self.sw2.items)} ")
            packet.src = packet.dst
            yield env.timeout(transmission_delay)
            yield sw.put(packet)
            # if packet.dst == "switch1":
            #     yield self.sw1.put(packet)
            # else:
            #     yield self.sw2.put(packet)

    def step(self,action,sw):
        actions_step ={0:"switch1",1:"switch2",2:"dest"}
        if actions_step[action] == sw:
            return [len(self.sw1.items),len(self.sw2.items)] , 0,False,False
        elif actions_step[action] != sw:
            packet =yield sw.get()
            transmission_delay = packet_size/self.link_speeds[sw][actions_step[action]]
            yield self.env.timeout(transmission_delay)
            if sw == "switch2":
                packet.current = "switch2"
                yield self.sw2.put(packet)
                
                if len(self.sw1.items) > len(self.sw2.items):
                    print("packet sent to switch 2 ")
                    return [len(self.sw1.items),len(self.sw2.items)] , 1,False,False
                else:
                    print("packet sent to switch 2 ")
                    return [len(self.sw1.items),len(self.sw2.items)] ,-10,False,False
               
            else:
                packet.current = "switch1"
                yield self.es3.put(packet)
                if len(self.sw1.items) < len(self.sw2.items):
                    print("packet sent to switch 1 ")
                    return [len(self.sw1.items),len(self.sw2.items)] ,1,False,False
                else:
                    print("packet sent to switch 1 ")
                    return  [len(self.sw1.items),len(self.sw2.items)] ,-10,False,False
                
             

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
            packet = Packet(packet_id,"es1" ,src, dst)
            yield host.put(packet)
            packet_id += 1

    def create_environment(self,time):
        """
        Sets up the network environment with processes.
        """
        host_process1 = self.env.process(self.packet_generator(self.env, "es1", "switch1", self.es1))
        host_process2 = self.env.process(self.packet_generator(self.env, "es2", "switch2", self.es2))
        switch_process1 = self.env.process(self.switch(self.env, self.es1, self.sw1,self.link_speeds["sw1"]["es1"]))
        self.env.process(self.send_packet_to_es3(self.env, self.es3,self.sw1,self.link_speeds["sw1"]["dest"]))
        switch_process2 = self.env.process(self.switch(self.env,self.es2,self.sw2,self.link_speeds["sw2"]["es2"]))
        self.env.process(self.send_packet_to_es3(self.env,self.es3,self.sw2,self.link_speeds["sw1"]["dest"]))
        self.env.run(until=time)
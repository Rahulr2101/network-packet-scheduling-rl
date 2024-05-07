import simpy
import uuid
import tabulate


packet_size = 1000
packet_time = 6

class Packet:
    def __init__(self, id, src,dst,timestamp):
        self.id = id
        self.src = src
        self.dst = dst
        self.timestamp = timestamp
       

class NetworkEnvironment:
    def __init__(self, env, link_speeds={"sw1":{"es1":1000,"dest":100,"sw2":800}, "sw2":{"es2":400,"dest":100,"sw1":800}}):
        self.env = env
        self.max_capacity = 30
        self.es1 = simpy.Store(self.env, capacity=self.max_capacity)
        self.es2 = simpy.Store(self.env, capacity=self.max_capacity )
        self.es3 = simpy.Store(self.env, capacity=self.max_capacity )
        self.sw1 = simpy.Store(self.env, capacity=self.max_capacity )
        self.sw2 = simpy.Store(self.env, capacity=self.max_capacity )
        self.actions_step ={0:"sw1_to_sw2",1:"sw2_to_sw1",2:"sw1_to_dest",3:"sw2_to_dest"}
        self.link_speeds = link_speeds
        self.logs_list = []
        # self.create_environment(time)


    def switch(self,es,sw,speed):
        """
        Simulates packet switching behavior.
        """
        while True:
            packet = yield es.get()
            transmission_delay = packet_size / speed
            self.logs_list.append([packet.id,packet.src +" to " + packet.dst,transmission_delay,self.env.now,len(self.sw1.items),len(self.sw2.items) ])
            packet.src = packet.dst
            yield self.env.timeout(transmission_delay)
            yield sw.put(packet)


    def reward(self,packet):
        reward = 0
        if packet.timestamp + 20  <  self.env.now :
            return 2
        else:
            return -8

    def CalculateTransmissionDelay(speed):
        return packet_size/speed



    def step(self,action):
        if self.actions_step[action] == self.actions_step[0]:
            packet = yield self.sw1.get()
            print(self.env.now)
            yield self.env.timeout(self.CalculateTransmissionDelay(self.link_speeds["sw1"]["sw2"]))
            yield self.sw2.put(packet)
            print(self.env.now)
            print(f"Sending packet to sw1 to sw2 ; sw1 Queue {len(self.sw1.items)} sw2 Queue {len(self.sw2.items)}")
        self.env.run()
        return [len(self.sw1.items),len(self.sw2.items),self.reward(packet)]
        # if action_step == "sw1":

        

    def send_packet_to_es3(self, env, es, sw, speed):
        """
        Sends packets received by the switch to es3.
        """
        while True:
            packet = yield sw.get()
            transmission_delay = packet_size / speed
            packet.dst = "es3"
            self.logs_list.append([packet.id,packet.src +" to " + "es3",transmission_delay,self.env.now,len(self.sw1.items),len(self.sw2.items) ])
            yield env.timeout(transmission_delay)
            yield es.put(packet)

    def packet_generator(self, src, dst, host, packet_number=5):
        while packet_number > 0:
            packet = Packet(uuid.uuid4(),src, dst,timestamp= self.env.now)
            yield host.put(packet)
            packet_number -= 1
            yield self.env.timeout(5)

            
    def display(self):
        print(tabulate.tabulate(self.logs_list, headers=["Packet ID", "Action", "Delay(in Sec)", "Current_time(in Sec)", "Switch 1 Queue Length", "Switch 2 Queue Length"]))


    
    # def create_environment(self,time):
    #     """
    #     Sets up the network environment with processes.
    #     """
    #     host_process1 = self.env.process(self.packet_generator( "es1", "switch1", self.es1))
    #     host_process2 = self.env.process(self.packet_generator( "es2", "switch2", self.es2))
    #     switch_process1 = self.env.process(self.switch( self.es1, self.sw1,self.link_speeds["sw1"]["es1"]))
    #     # self.env.process(self.send_packet_to_es3(self.env, self.es3,self.sw1,self.link_speeds["sw1"]["dest"]))
    #     switch_process2 = self.env.process(self.switch(self.es2,self.sw2,self.link_speeds["sw2"]["es2"]))
    #     # self.env.process(self.send_packet_to_es3(self.env,self.es3,self.sw2,self.link_speeds["sw1"]["dest"]))
        
        
env =  simpy.Environment()
nw = NetworkEnvironment(env)
host_process1 = env.process(nw.packet_generator( "es1", "switch1", nw.es1))
host_process2 = env.process(nw.packet_generator("es2","switch2",nw.es2))
switch_process1 = env.process(nw.switch( nw.es1, nw.sw1,nw.link_speeds["sw1"]["es1"]))
switch_process2 = env.process(nw.switch(nw.es2,nw.sw2,nw.link_speeds["sw2"]["es2"]))
env.run(until = 20)
nw.display()
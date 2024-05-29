import simpy
import uuid
import tabulate



class Packet:
    def __init__(self, id, src,dst,timestamp,packet_size):
        self.id = id
        self.src = src
        self.dst = dst
        self.timestamp = timestamp
        self.packet_size = packet_size
       

class NetworkEnvironment:
    def __init__(self, env, link_speeds={"sw1":{"es1":900,"dest":100,"sw2":900}, "sw2":{"es2":600,"dest":500,"sw1":900}}):
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


    def switch(self,es,sw,speed,):
        """
        Simulates packet switching behavior.
        """
        while True:
            packet = yield es.get()
            transmission_delay = packet.packet_size / speed
            self.logs_list.append([packet.id,packet.src +" to " + packet.dst,transmission_delay,self.env.now,len(self.sw1.items),len(self.sw2.items) ])
            packet.src = packet.dst
            yield self.env.timeout(transmission_delay)
            yield sw.put(packet)

    # def CalculateTransmissionDelay(speed):
    #     return packet_size/speed

        

    def send_packet_to_es3(self, env, es, sw, speed):
        """
        Sends packets received by the switch to es3.
        """
        while True:
            packet = yield sw.get()
            transmission_delay = packet.packet_size / speed
            packet.dst = "es3"
            self.logs_list.append([packet.id,packet.src +" to " + "es3",f"{transmission_delay}   {packet.timestamp}",self.env.now,len(self.sw1.items),len(self.sw2.items) ])
            yield env.timeout(transmission_delay)
            yield es.put(packet)

    def packet_generator(self, src, dst, host,packet_size,packet_number=10):
        while packet_number >0:
            packet = Packet(uuid.uuid4(),src, dst,timestamp= self.env.now,packet_size=packet_size)
            yield host.put(packet)
            packet_number -= 1
            yield self.env.timeout(1)

            
    def display(self):
        print(tabulate.tabulate(self.logs_list, headers=["Packet ID", "Action", "Delay(in Sec)", "Current_time(in Sec)", "Switch 1 Queue Length", "Switch 2 Queue Length"]))
        
        
env =  simpy.Environment()
nw = NetworkEnvironment(env)
host_process1 = env.process(nw.packet_generator( "es1", "switch1", nw.es1,packet_size=1000))
host_process2 = env.process(nw.packet_generator( "es2", "switch2", nw.es2,packet_size=1000))
switch_process1 = env.process(nw.switch( nw.es1, nw.sw1,nw.link_speeds["sw1"]["es1"]))
env.process(nw.send_packet_to_es3(env, nw.es3,nw.sw1,nw.link_speeds["sw1"]["dest"]))
switch_process2 = env.process(nw.switch(nw.es2,nw.sw2,nw.link_speeds["sw2"]["es2"]))
env.process(nw.send_packet_to_es3(env,nw.es3,nw.sw2,nw.link_speeds["sw1"]["dest"]))
env.run(until = 1000)
nw.display()
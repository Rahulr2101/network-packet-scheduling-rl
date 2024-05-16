import simpy
import uuid
import tabulate
import numpy as np
import random


packet_size = 1000
packet_time = 6
logs_list = []
num_states = 91
num_actions = 4

# Create a NumPy array with zeros for 91 states and 4 actions
array_shape = (num_states, num_actions)


q = np.zeros((30, 30,4))

class Packet:
    def __init__(self, id, src,dst,timestamp):
        self.id = id
        self.src = src
        self.dst = dst
        self.timestamp = timestamp
       

class NetworkEnvironment:
    def __init__(self, env, link_speeds={"sw1":{"es1":900,"es3":100,"sw2":800}, "sw2":{"es2":400,"es3":1000,"sw1":800}}):
        self.env = env
        self.max_capacity = 30
        self.es1 = simpy.Store(self.env, capacity=self.max_capacity)
        self.es2 = simpy.Store(self.env, capacity=self.max_capacity )
        self.es3 = simpy.Store(self.env, capacity=1000000 )
        self.sw1 = simpy.Store(self.env, capacity=self.max_capacity )
        self.sw2 = simpy.Store(self.env, capacity=self.max_capacity )
        self.actions_step ={0:"sw1_to_sw2",1:"sw2_to_sw1",2:"sw1_to_dest",3:"sw2_to_dest"}
        self.link_speeds = link_speeds  
        

    def switch(self,es,sw,speed):
        """
        Simulates packet switching behavior.
        """
        self.flag = True
        while self.flag:
            packet = yield es.get()
            transmission_delay = packet_size / speed
            logs_list.append([packet.id,packet.src +" to " + packet.dst,transmission_delay,env.now -packet.timestamp,env.now,len(self.sw1.items),len(self.sw2.items) ])
            packet.src = packet.dst
            yield env.timeout(transmission_delay)
            yield sw.put(packet)

    # def send_packet_to_es3(self, env, es, sw, speed):
    #     """
    #     Sends packets received by the switch to es3.
    #     """
    #     while True:
    #         packet = yield sw.get()
    #         transmission_delay = packet_size / speed
    #         packet.dst = "es3"
    #         self.logs_list.append([packet.id,packet.src +" to " + "es3",transmission_delay,packet.timestamp,self.env.now,len(self.sw1.items),len(self.sw2.items) ])
    #         yield env.timeout(transmission_delay)
    #         yield es.put(packet)

    def packet_generator(self, src, dst, host, packet_number=10):
        while packet_number >0:
            packet = Packet(uuid.uuid4(),src, dst,timestamp= self.env.now)
            yield host.put(packet)
            packet_number -= 1
            yield self.env.timeout(1)

            
def display():
        print(tabulate.tabulate(logs_list, headers=["Packet ID", "Action", "Delay(in Sec)", "Packet Time","Current_time(in Sec)", "Switch 1 Queue Length", "Switch 2 Queue Length"]))
    

def CalculateTransmissionDelay(speed):
        return packet_size/speed      
      
def rewardCal(now, timestamp):
        reward = 0
        if timestamp + 20  < now :
            return 2
        else:
            return -8
        
def model(env):
     
       
        episodes = 1000
        learning_rate_a = 0.9
        discount_factor_g = 0.9
        epsilon = 1
        epsilon_decay_rate = 0.0001
        rng = np.random.default_rng()
        rewards_per_episode = np.zeros(episodes)
        start = 0
        

        # print(q)
        
       
        for i in range(episodes):
            
            
            
            # Starting network switches and packet generator
            logs_list.append([f"episode = {i} ","","","","","",""])  
           
            nw = NetworkEnvironment(env)
            host_process1 = env.process(nw.packet_generator( "es1", "switch1", nw.es1))
            host_process2 = env.process(nw.packet_generator("es2","switch2",nw.es2))
            switch_process1 = env.process(nw.switch( nw.es1, nw.sw1,nw.link_speeds["sw1"]["es1"]))
            switch_process2 = env.process(nw.switch(nw.es2,nw.sw2,nw.link_speeds["sw2"]["es2"]))
           
            
            yield env.timeout(10)     
            start += 100 
            state = [len(nw.sw1.items),len(nw.sw2.items)]
            while  env.now < start and (len(nw.es1.items) != 0 or len(nw.es2.items) != 0) :
                yield env.timeout(1)
                if rng.random()< epsilon:
                    print(f'value = {len(list(nw.actions_step.keys()))}')
                    action = random.randint(0,len(list(nw.actions_step.keys()))-1)
                else:
                    action = np.argmax(q[state,:])
                print(state)
                print(q[state, :])
                print(f'action = {action}')
                return
                if nw.actions_step[action] == "sw1_to_sw2":
                    packet =  yield nw.sw1.get()
                    yield nw.sw2.put(packet)
                    logs_list.append([packet.id,"sw1" +" to " + "sw2",f"{CalculateTransmissionDelay(nw.link_speeds["sw1"]["sw2"])} (Agent)",env.now - packet.timestamp,env.now,len(nw.sw1.items),len(nw.sw2.items) ])
                    

                    
                elif nw.actions_step[action]=="sw2_to_sw1" :
                    packet = yield nw.sw2.get()
                    yield nw.sw1.put(packet)
                    
                    logs_list.append([packet.id,"sw2" +" to " + "sw1",f"{CalculateTransmissionDelay(nw.link_speeds["sw2"]["sw1"])} (Agent)",env.now - packet.timestamp,env.now,len(nw.sw1.items),len(nw.sw2.items) ])

                    
                elif nw.actions_step[action] == "sw1_to_dest":
                    packet = yield nw.sw1.get()
                    yield nw.es3.put(packet)
                    
                    logs_list.append([packet.id,"sw1" +" to " + "es3",f"{CalculateTransmissionDelay(nw.link_speeds["sw1"]["es3"])} (Agent)",env.now-packet.timestamp,env.now,len(nw.sw1.items),len(nw.sw2.items) ])

                    
                elif nw.actions_step[action] == "sw2_to_dest":
                    packet = yield nw.sw2.get()
                    yield nw.es3.put(packet)
                    logs_list.append([packet.id,"sw2" +" to " + "es3",f"{CalculateTransmissionDelay(nw.link_speeds["sw2"]["es3"])} (Agent)",env.now-packet.timestamp,env.now,len(nw.sw1.items),len(nw.sw2.items) ])
                    
                # print(i,len(nw.sw1.items),len(nw.sw2.items),len(nw.es3.items),(len(nw.sw1.items) > 0  or len(nw.sw2.items) > 0 ))    
                new_state = [len(nw.sw1.items),len(nw.sw2.items)]
                reward = rewardCal(env.now,packet.timestamp)
                
                q[state,action] = q[state,action] + learning_rate_a * (
                    reward + discount_factor_g * np.max(q[new_state,:]) - q[state,action])
                state = new_state
            epsilon = max(epsilon - epsilon_decay_rate, 0)
            # nw.flag = False
            
            if(epsilon==0):
                learning_rate_a = 0.0001    
            # print("he")
            # if reward == 1:
            #     print("hello")
            #     rewards_per_episode[i] = 1
                
def printer():
    while True:
        yield env.timeout(1)
        print(env.now)
     
env =  simpy.Environment()

model_process = env.process(model(env))
# env.process(printer())
env.run(until =100000)
display()
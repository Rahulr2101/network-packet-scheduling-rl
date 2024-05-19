import simpy
import uuid
import tabulate
import numpy as np
import random
import matplotlib.pyplot as plt

packet_size = 1000
packet_time = 6
logs_list = []
episodes = 35000
rewards_per_episode = np.zeros(episodes)
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
      
def rewardCal(now, timestamp,action,nw):
        overtime_threshold = 30
       
       
        if action == 2 or action == 3:
            if timestamp + overtime_threshold > now :
                return 10
            else:
                return -1 * (now - (timestamp + overtime_threshold))
        else:
            if action == 0 and len(nw.sw1.items) >= len(nw.sw2.items):
                return 2
            elif action == 2 and len(nw.sw2.items) >= len(nw.sw1.items):
                return 2
            else:
                return -1
                    
        
def model(env):
     
        learning_rate_a = 0.9
        discount_factor_g = 0.9
        epsilon = 1
        epsilon_decay_rate = 0.0000303
        rng = np.random.default_rng()
        start = 0
        

       
        for i in range(episodes):
            
            
            
            # Starting network switches and packet generator
            logs_list.append([f"episode = {i} ","","","","","",""])  
           
            nw = NetworkEnvironment(env)
            host_process1 = env.process(nw.packet_generator( "es1", "switch1", nw.es1))
            host_process2 = env.process(nw.packet_generator("es2","switch2",nw.es2))
            switch_process1 = env.process(nw.switch( nw.es1, nw.sw1,nw.link_speeds["sw1"]["es1"]))
            switch_process2 = env.process(nw.switch(nw.es2,nw.sw2,nw.link_speeds["sw2"]["es2"]))
            episode_reward = 0
            
            yield env.timeout(5)     
            start += 100 
            state = [len(nw.sw1.items),len(nw.sw2.items)]
            while  env.now < start:
                
                yield env.timeout(1)
                if rng.random()< epsilon:
                    action = random.randint(0,len(list(nw.actions_step.keys()))-1)
                else:
                    action = np.argmax(q[state[0],state[1],:])
                
                
                if len(nw.sw1.items) == 0 and (action == 0 or action == 2):
                    continue
                if len(nw.sw2.items) == 0 and (action == 1 or action == 3):
                    continue
                
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
                new_state = [len(nw.sw1.items),len(nw.sw2.items)]
                print(action)
                reward = rewardCal(env.now,packet.timestamp,action,nw)
                episode_reward += reward
                
                q[state[0],state[1],action] = q[state[0],state[1],action] + learning_rate_a * (
                    reward + discount_factor_g * np.max(q[new_state[0],state[1],:]) - q[state[0],state[1],action])
                state = new_state
            epsilon = max(epsilon - epsilon_decay_rate, 0)
            rewards_per_episode[i] = episode_reward
            if(epsilon==0):
                learning_rate_a = 0.0001
                
        
        

     
env =  simpy.Environment()

model_process = env.process(model(env))
env.run(until =20010000)
# display()

sum_rewards = np.zeros(episodes)
for t in range(episodes):
    sum_rewards[t] = np.sum(rewards_per_episode[max(0, t-100):(t+1)])

plt.plot(sum_rewards, label="Rewards per Episode")
plt.xlabel("Episode")
plt.ylabel("Total Reward")
plt.title("Rewards Collected per Episode")
plt.legend()
plt.savefig('model2.png')
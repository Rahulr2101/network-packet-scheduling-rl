import simpy


packet_size = 1000

class Packet:
    def __init__(self,id,src,dst):
        self.id = id
        self.src = src
        self.dst = dst

def switch(env,es,speed):
    
    while True:
        packet = yield es.get()
        transmission_delay = packet_size / speed
        print(f"Transmitting packet{packet.id} from {packet.src} to {packet.dst} - Delay: {transmission_delay:.4f} seconds  - Current time:{env.now} seconds - Current Switch 1 Queue Length: {len(sw1.items)}') - Current Switch 2 Queue Length: {len(sw2.items)} ")
        packet.src = packet.dst
        yield env.timeout(transmission_delay)
        if packet.dst == "switch1":
            yield sw1.put(packet)
        else:
            yield sw2.put(packet)
        
def send_packet_to_es3(env,es,sw,speed):
    '''
    Sends packets received by the switch to es3.
    '''
    while True:
        packet = yield sw.get()
        transmission_delay = packet_size/speed
        print(f"Transmitting packet{packet.id} from {packet.src} to es3 - Delay: {transmission_delay:.4f} seconds - Current time:{env.now} seconds")
        yield env.timeout(transmission_delay)
        yield es.put(packet)

def packet_generator(env,src,dst,host):
    packet_id = 1
    while True:
        
        packet = Packet(packet_id,src,dst)
        yield host.put(packet)
        packet_id += 1

env = simpy.Environment()

es1 = simpy.Store(env,capacity=10)
es2 = simpy.Store(env,capacity=10)
es3 = simpy.Store(env,capacity=10)
sw1 = simpy.Store(env,capacity=10)
sw2 = simpy.Store(env,capacity=10)

'''
Generates packets with increasing IDs at a specified interval
'''
host_process1 = env.process(packet_generator(env,"es1","switch1", es1))
host_process2 = env.process(packet_generator(env,"es2","switch2",es2))

link_speed1 = 1000  
link_speed2 = 300 
link_speed3 = 400  
link_speed4 = 800 
link_speed5 = 200

switch_process1 = env.process(switch(env, es1, link_speed1))
env.process(send_packet_to_es3(env,es3,sw1,link_speed2))
switch_process2 = env.process(switch(env, es2, link_speed3))
env.process(send_packet_to_es3(env,es3,sw2,link_speed5))
env.run(until=100) 


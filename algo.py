import numpy as np


from nw_environment import NetworkEnvironment


env = NetworkEnvironment(100)  


action = env.step(0)
print(action)



from agent import Agent
from controler import Controler
import aircv

agent = Agent(dev_ip="10.254.46.45")
controler = Controler(agent)

controler.swipe((0,0), (550,0))
print controler.get_display_info()

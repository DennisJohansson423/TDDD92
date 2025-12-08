from run_sc2 import run_sc2
from agents.basic_agent import BasicAgent
from config import MAPS
import sys

from commandcenter import Unit
sys.path.append(".")  # Needed to find commandcenter if running from terminal
from commandcenter import Race




if __name__ == "__main__":
    run_sc2(
        bot1=BasicAgent(),
        race1=Race.Terran,
        maps=MAPS,
        real_time=False)

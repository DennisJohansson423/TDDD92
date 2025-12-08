# The path to your SC2_x64 executable. This will be specific to your computer:
#SC2_PATH = r"d:\StarCraft II\Versions\Base81009\SC2_x64.exe"
SC2_PATH = r"d:\StarCraft II\Versions\Base81009\SC2_x64.exe"

# Example : SC2_PATH = r"C:\Program Files (x86)\StarCraft II\Versions\Base75025\SC2_x64.exe"

MAPS = ["InterloperTest.SC2Map"]

# Give resources and allows fast building, good for testing
DEBUG_CHEATS = False
# Debug prints to console
DEBUG_CONSOLE = False
# Log information such as computation time per step
# Note: The game needs to end in order for the log file to be saved! You can surrender the game.
DEBUG_LOGS = False
# Text on screen showing build order and tasks
DEBUG_TEXT = False
# Units information displayed on screen
DEBUG_UNIT = True	
# Enable visual debugger
DEBUG_VISUAL = False

# How many frames between actions
FRAME_SKIP = 10

# Path to build order
BUILD_ORDER_PATH = "builds/labs_build_order"
# Path to DFBB build order
DFBB_BUILD_ORDER_PATH = "builds/DFBB_build_order"

USE_RESOURCE_MANAGER = False
USE_BOIDS_POTENTIAL = True
USE_BAYESIAN_NETWORK = False
USE_FLOOD_FILL = True
USE_DEBUG_FLOOD_FILL = True
USE_NAVIGATION = False
USE_POTENTIAL_FLOW = False
USE_DFBB = True
DFBB_INSTEAD_OF_HARDCODE = False


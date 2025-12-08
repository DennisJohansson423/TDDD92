from modules.flood_fill import FloodFill
from visualdebugger.visualize_flood_fill import VisualizeFloodFill

if __name__ == "__main__":
    flood_fill = FloodFill()
    vizualise_flood_fill = VisualizeFloodFill(flood_fill, cell_size=5, alongside_game=False)
    vizualise_flood_fill.display_map()
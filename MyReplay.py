import sc2reader






replay = sc2reader.load_replay("./hello")
print(f"Game Version: {replay.release_string}")
print(f"Map: {replay.map_name}")
print(f"Players: {[player.name for player in replay.players]}")

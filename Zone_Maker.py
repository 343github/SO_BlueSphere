import os
import struct
from PIL import Image, ImageDraw

def read_u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]

def get_neighbors(map_struct):
    neighbors = []
    for i in range(4):
        n = read_u16(map_struct, 1 + 2*i)
        n = n & 0x7FFF  # Ignore the highest bit
        if n < 1545:  # Maps
            neighbors.append(n)
        else:
            neighbors.append(None)
    return neighbors

def create_zone_image(start_map_id, all_maps, visited=None, offset=(0, 0), positions=None):
    if visited is None:
        visited = set()

    if positions is None:
        positions = {}

    if start_map_id in visited:
        return None, set(), positions

    visited.add(start_map_id)

    try:
        map_struct = all_maps[start_map_id]
        neighbors = get_neighbors(map_struct)
        
        # Load map image
        map_image = Image.open(f"map_images/map_{start_map_id:04d}.png").convert('RGBA')
        
        # Save current map position
        positions[start_map_id] = (offset[0], offset[1])

        # Add neighboring maps
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # Clockwise Up, Right, Down, Left
        for i, neighbor_id in enumerate(neighbors):
            if neighbor_id is not None and neighbor_id not in visited:
                dx, dy = directions[i]
                neighbor_offset = (offset[0] + dx * map_image.width, offset[1] + dy * map_image.height)
                _, neighbor_visited, positions = create_zone_image(neighbor_id, all_maps, visited, neighbor_offset, positions)
                visited.update(neighbor_visited)
        
        return None, visited, positions

    except FileNotFoundError:
        print(f"Warning: Image for map {start_map_id} not found.")
        return None, visited, positions

def extract_and_visualize_zones():
    os.makedirs("zone_images", exist_ok=True)
    all_visited = set()

    # Load all maps into memory
    all_maps = {}
    for map_id in range(1545):  # Maps
        try:
            with open(f"maps/map_{map_id:04d}_struct.bin", "rb") as f:
                all_maps[map_id] = f.read()
        except FileNotFoundError:
            print(f"Warning: Struct for map {map_id} not found.")

    # Create a dictionary to track zones
    zones = {}

    for start_map_id in range(1545):
        if start_map_id not in all_visited:
            print(f"Processing zone starting with map {start_map_id}")
            _, visited, positions = create_zone_image(start_map_id, all_maps)

            if visited:
                zone_id = min(visited)  # Uses the lowest ID as the zone identifier.

                # Obtain the size of the map.
                map_image = Image.open(f"map_images/map_{zone_id:04d}.png").convert('RGBA')

                # Calculate image size
                min_x = min(pos[0] for pos in positions.values())
                min_y = min(pos[1] for pos in positions.values())
                max_x = max(pos[0] for pos in positions.values())
                max_y = max(pos[1] for pos in positions.values())

                total_width = max_x - min_x + map_image.width
                total_height = max_y - min_y + map_image.height

                zone_image = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))

                for map_id, pos in positions.items():
                    map_image = Image.open(f"map_images/map_{map_id:04d}.png").convert('RGBA')
                    zone_image.paste(map_image, (pos[0] - min_x, pos[1] - min_y))

                zone_image.save(f"zone_images/zone_{zone_id:04d}.png")
                zones[zone_id] = visited
                all_visited.update(visited)

    # Print zone information
    for zone_id, maps in zones.items():
        print(f"Zone {zone_id} contains maps: {sorted(maps)}")

def main():
    extract_and_visualize_zones()
    print("Zone images created and saved in zone_images folder")

if __name__ == "__main__":
    main()

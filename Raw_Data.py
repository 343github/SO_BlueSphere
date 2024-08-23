"""
Made by 343 - 2024
Based on the work done by scurest 
"""

import os
import struct

def read_u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]

def rom1_offset(bank, addr):
    assert 0x4000 <= addr < 0x8000, "address not in ROM1"
    return 0x4000 * bank + (addr - 0x4000)

def tileset_offset(tileset_id):
    bank = 0x40 + tileset_id // 5
    addr = 0x4001 + (tileset_id % 5) * 0x0C40
    return rom1_offset(bank, addr)

def extract_tilesets(rom_data):
    os.makedirs("tilesets", exist_ok=True)
    for tileset_id in range(98):  # Tileset number all 98
        offset = tileset_offset(tileset_id)
        tiles = rom_data[offset:offset + 0xC00]
        palettes = rom_data[offset + 0xC00:offset + 0xC40]
        
        with open(f"tilesets/tileset_{tileset_id:02d}_tiles.bin", "wb") as f:
            f.write(tiles)
        with open(f"tilesets/tileset_{tileset_id:02d}_palettes.bin", "wb") as f:
            f.write(palettes)

def extract_maps(rom_data):
    os.makedirs("maps", exist_ok=True)
    
    for map_id in range(1545):  # Maps number
        if map_id < 800:
            bank = 0x54
            addr = 0x4001 + 0x14 * map_id
        else:
            bank = 0x55
            addr = 0x4001 + 0x14 * (map_id - 800)
        
        offset = rom1_offset(bank, addr)
        map_struct = rom_data[offset:offset + 0x14]
        
        with open(f"maps/map_{map_id:04d}_struct.bin", "wb") as f:
            f.write(map_struct)
        
        # Extract map data location
        data_offset = rom1_offset(0x5A, 0x4001 + 3 * map_id)
        addr = read_u16(rom_data, data_offset)
        bank = rom_data[data_offset + 2]
        
        map_data_offset = rom1_offset(bank, addr)
        map_data = rom_data[map_data_offset:map_data_offset + 1024]
        
        with open(f"maps/map_{map_id:04d}_data.bin", "wb") as f:
            f.write(map_data)

def main():
    with open("sobs.gbc", "rb") as f:
        rom_data = f.read()
    
    extract_tilesets(rom_data)
    extract_maps(rom_data)

if __name__ == "__main__":
    main()

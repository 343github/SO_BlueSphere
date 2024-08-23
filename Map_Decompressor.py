import os
import struct
from PIL import Image

def read_u16(data, offset):
    return struct.unpack_from("<H", data, offset)[0]

def decode_map_tiles(input_data):
    output = bytearray(20 * 18)
    i, j = 0, 0

    try:
        while j < len(output):
            if i >= len(input_data):
                print(f"Reached end of input data at j={j}")
                break
            a = input_data[i]
            i += 1

            if a & 0x80 == 0 or a >= 0xA0:
                output[j] = a
                j += 1
            elif a & 0x10 != 0:
                count = (a & 0xF) + 2
                for _ in range(count):
                    if j == 0:
                        output[j] = 0
                    else:
                        output[j] = (output[j - 1] + 1) & 0xFF
                    j += 1
            else:
                count = (a & 0xF) + 2
                for _ in range(count):
                    if j == 0:
                        output[j] = 0
                    else:
                        output[j] = output[j - 1]
                    j += 1

    except Exception as e:
        print(f"Error in decode_map_tiles: {e}")
        print(f"i={i}, j={j}, len(input_data)={len(input_data)}")

    return bytes(output[:j]), i

def decode_map_attribs(input_data):
    output = bytearray(20 * 19)
    i, j = 0, 0

    try:
        while j < 20 * 19 and i < len(input_data):
            a = input_data[i]
            i += 1

            if a & 0x6 != 0x6:
                output[j] = a
                j += 1
            else:
                count = ((a >> 4) | ((a & 1) << 4)) + 2
                for _ in range(count):
                    if j >= 20 * 19:
                        break
                    output[j] = output[j - 1] if j > 0 else 0
                    j += 1

        if j < 20 * 19:
            print(f"Warning: Not enough attribute data. Expected 380, got {j}")

    except Exception as e:
        print(f"Error in decode_map_attribs: {e}")
        print(f"i={i}, j={j}, len(input_data)={len(input_data)}")

    return bytes(output[:j])

def get_tileset(tileset_id):
    with open(f"tilesets/tileset_{tileset_id:02d}_tiles.bin", "rb") as f:
        tiles = f.read()
    with open(f"tilesets/tileset_{tileset_id:02d}_palettes.bin", "rb") as f:
        palettes = f.read()
    return tiles, palettes

def draw_tile(image, tile, palette, x, y):
    for dy in range(8):
        for dx in range(8):
            mask = 1 << (7 - dx)
            lo = (tile[dy*2] & mask) != 0
            hi = (tile[dy*2+1] & mask) != 0
            color_num = lo | (hi << 1)
            
            bgr = read_u16(palette, 2 * color_num)
            r = ((bgr >> 0) & 0x1F) * 255 // 31
            g = ((bgr >> 5) & 0x1F) * 255 // 31
            b = ((bgr >> 10) & 0x1F) * 255 // 31
            
            image.putpixel((x + dx, y + dy), (r, g, b))

def create_map_image(map_id):
    try:
        with open(f"maps/map_{map_id:04d}_struct.bin", "rb") as f:
            map_struct = f.read()
        
        with open(f"maps/map_{map_id:04d}_data.bin", "rb") as f:
            map_data = f.read()

        tileset_id = map_struct[0]
        tiles, palettes = get_tileset(tileset_id)

        tile_nums, i = decode_map_tiles(map_data)
        attribs = decode_map_attribs(map_data[i:])

        print(f"Map {map_id}: tile_nums length = {len(tile_nums)}, attribs length = {len(attribs)}")

        image = Image.new('RGB', (20 * 8, 18 * 8))

        for i in range(min(20 * 18, len(tile_nums), len(attribs))):
            tile_num = tile_nums[i]
            palette_num = attribs[i] & 7

            tile_num = struct.unpack('b', bytes([tile_num]))[0]
            addr = 0x9000 + tile_num * 16
            if not (0x8C00 <= addr < 0x9800):
                print(f"Invalid tile address: {addr:04X} for tile_num {tile_num}")
                continue

            ofs = addr - 0x8C00
            if ofs + 16 > len(tiles):
                print(f"Tile offset out of range: ofs={ofs}, len(tiles)={len(tiles)}")
                continue

            tile = tiles[ofs:ofs + 16]

            pal_ofs = 8 * palette_num
            if pal_ofs + 8 > len(palettes):
                print(f"Palette offset out of range: pal_ofs={pal_ofs}, len(palettes)={len(palettes)}")
                continue

            palette = palettes[pal_ofs:pal_ofs + 8]

            x = (i % 20) * 8
            y = (i // 20) * 8

            draw_tile(image, tile, palette, x, y)

        os.makedirs("map_images", exist_ok=True)
        image.save(f"map_images/map_{map_id:04d}.png")

    except Exception as e:
        print(f"Error processing map {map_id}: {e}")

def main():
    for map_id in range(1545):
        print(f"Processing map {map_id}")
        create_map_image(map_id)

if __name__ == "__main__":
    main()


import math

def calculate_polygons(startx, starty, endx, endy, radius):
    def hexagon_coords(center_x, center_y, radius):
        angle = 0
        coords = []
        for _ in range(6):
            x = center_x + radius * math.cos(math.radians(angle))
            y = center_y + radius * math.sin(math.radians(angle))
            coords.append((x, y))
            angle += 60
        return coords

    starty_adj = starty - radius * 1.5
    endy_adj = endy + radius * 1.5
    x_offset = radius * math.sqrt(3)

    polygons = []
    row = 0
    while starty_adj <= endy_adj:
        is_even_row = row % 2 == 0
        startx_adj = startx - (radius if is_even_row else 0)
        while startx_adj <= endx + x_offset:
            center_x = startx_adj + radius * 1.5
            center_y = starty_adj + radius * math.sqrt(3) / 2
            hexagon = hexagon_coords(center_x, center_y, radius)
            polygons.append(hexagon)
            startx_adj += x_offset * 2

        starty_adj += radius * math.sqrt(3)
        row += 1

    return polygons

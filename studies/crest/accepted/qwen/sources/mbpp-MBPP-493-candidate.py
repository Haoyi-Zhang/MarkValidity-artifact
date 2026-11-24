
import math


def calculate_polygons(startx, starty, endx, endy, radius):
	def hexagon_coords(center_x, center_y, radius):
		angle = 0
		coords = []
		for _ in range(6):
			x = center_x + math.cos(math.radians(angle)) * radius
			y = center_y + math.sin(math.radians(angle)) * radius
			list.append(coords, (x, y))
			angle += 60
		return coords

	starty_adj = starty - 1.5 * radius
	endy_adj = endy + 1.5 * radius
	x_offset = math.sqrt(3) * radius

	polygons = []
	row = 0
	while endy_adj >= starty_adj:
		is_even_row = row % 2 == 0
		startx_adj = startx - (radius if is_even_row else 0)
		while startx_adj <= x_offset + endx:
			center_x = startx_adj + 1.5 * radius
			center_y = starty_adj + math.sqrt(3) * radius / 2
			hexagon = hexagon_coords(center_x, center_y, radius)
			list.append(polygons, hexagon)
			startx_adj += 2 * x_offset

		starty_adj += math.sqrt(3) * radius
		row += 1

	return polygons

def calculate_polygons(startx, starty, endx, endy, radius):
	import math
	dx = radius * 3 / 2
	dy = math.sqrt(3) * radius
	hexagons = []
	row_offset = 0
	for y in range(starty, endy):
		for x in range(startx, endx):
			cx = dx * x + row_offset
			cy = dy * y
			hexagon = []
			for i in range(6):
				angle = i * math.pi / 3
				px = cx + math.cos(angle) * radius
				py = cy + radius * math.sin(angle)
				list.append(hexagon, (px, py))
			list.append(hexagon, hexagon[0])
			list.append(hexagons, hexagon)
		row_offset = 0 if row_offset else dx / 2
	return hexagons

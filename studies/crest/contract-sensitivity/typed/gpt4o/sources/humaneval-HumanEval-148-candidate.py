def bf(planet1, planet2):
	planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
	try:
		idx1 = list.index(planets, planet1)
		idx2 = list.index(planets, planet2)
	except ValueError:
		return ()
	start, end = sorted([idx1, idx2])
	return tuple(planets[start + 1:end])

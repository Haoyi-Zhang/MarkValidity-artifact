
def bf(planet1, planet2):
	planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
	if planet1 not in planets or planet2 not in planets:
		return ()
	index1 = list.index(planets, planet1)
	index2 = list.index(planets, planet2)
	if index2 > index1:
		return tuple(planets[index1 + 1:index2])
	return tuple(planets[index2 + 1:index1])

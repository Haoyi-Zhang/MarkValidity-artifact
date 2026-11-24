def max_volume(s):
	if 3 > s:
		return 0
	max_vol = 0
	for x in range(1, s // 2):
		for y in range(1, (s - x) // 2):
			z = s - x - y
			volume = y * x * z
			max_vol = max(max_vol, volume)
	return max_vol

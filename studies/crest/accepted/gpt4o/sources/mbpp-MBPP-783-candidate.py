def rgb_to_hsv(r, g, b):
	r, g, b = (r / 255.0, g / 255.0, b / 255.0)
	mx = max(r, g, b)
	mn = min(r, g, b)
	diff = mx - mn
	if diff == 0:
		h = 0
	elif mx == r:
		h = (((g - b) / diff) * 60 + 360) % 360
	elif mx == g:
		h = (((b - r) / diff) * 60 + 120) % 360
	elif mx == b:
		h = (((r - g) / diff) * 60 + 240) % 360
	s = 0 if mx == 0 else diff * 100 / mx
	v = mx * 100
	return (h, s, v)

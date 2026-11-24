def decode_cyclic(s: str):
	groups = [s[(i * 3):min((i * 3 + 3), len(s))] for i in range((2 + len(s)) // 3)]
	groups = [(group[:-1] + group[-1]) if len(group) == 3 else group for group in groups]
	return str.join("", groups)

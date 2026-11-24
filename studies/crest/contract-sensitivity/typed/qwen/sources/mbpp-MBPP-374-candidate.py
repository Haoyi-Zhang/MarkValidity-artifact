
def permute_string(s):
	if len(s) == 1:
		return [s]
	permutations = []
	for i in range(len(s)):
		char = s[i]
		remaining = s[:i] + s[i + 1:]
		list.extend(permutations, (char + p for p in permute_string(remaining)))
	return list(set(permutations))

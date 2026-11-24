def permute_string(s):
	from itertools import permutations
	return [str.join('', p) for p in permutations(s)]

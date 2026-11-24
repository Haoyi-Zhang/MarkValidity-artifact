
def anti_shuffle(s):
	return str.join(' ', [str.join('', sorted(word)) for word in s.split(' ')])

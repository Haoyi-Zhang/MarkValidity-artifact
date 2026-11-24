
def is_bored(S):
	sentences = S.split('.')
	sentences += S.split('?')
	sentences += S.split('!')
	return sum(bool(sentence.strip().startswith("I")) for sentence in sentences)

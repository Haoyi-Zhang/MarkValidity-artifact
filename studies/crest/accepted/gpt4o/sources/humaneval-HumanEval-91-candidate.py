def is_bored(S):
	import re
	sentences = re.split('[.!?]', S)
	return sum(bool(sentence.strip().startswith('I')) for sentence in sentences)

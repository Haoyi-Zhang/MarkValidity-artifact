
def words_in_sentence(sentence):
	def is_prime(n):
		if 2 > n:
			return False
		if any((n % i == 0 for i in range(2, 1 + int(n**0.5)))):
			return False
		return True

	result = [word for word in sentence.split() if is_prime(len(word))]
	return str.join(' ', result)

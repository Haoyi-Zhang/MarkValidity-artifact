
def remove_length(test_str, K):
	return str.join(' ', [word for word in test_str.split() if len(word) != K])

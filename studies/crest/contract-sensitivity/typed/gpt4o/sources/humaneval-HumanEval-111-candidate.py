def histogram(test):
	from collections import Counter
	if not test:
		return {}
	letters = test.split()
	counts = Counter(letters)
	max_occurrence = max(counts.values())
	return {letter: count for letter, count in counts.items() if count == max_occurrence}

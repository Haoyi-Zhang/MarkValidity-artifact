
from collections import Counter
import re


def n_common_words(text, n):
	words = re.findall(r'\b\w+\b', text.lower())
	word_counts = Counter(words)
	return word_counts.most_common(n)


import re


def num_position(text):
	match = re.search(r'\d+', text)
	if match:
		return match.start()
